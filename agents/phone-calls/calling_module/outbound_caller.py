"""
Outbound caller using ElevenLabs SDK.

Handles the actual call initiation and tracking.
"""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from .contracts import CallTask
from .config import get_config
from .observability import ObservabilityLogger


class OutboundCaller:
    """Handles outbound calls via ElevenLabs."""
    
    def __init__(self):
        self.logger = ObservabilityLogger()
        # In-memory storage for demo - in production, use Redis or database
        self._active_calls: Dict[str, Dict[str, Any]] = {}
        self._call_history: Dict[str, Dict[str, Any]] = {}
    
    def start_call(self, agent_id: str, agent_phone_number_id: str, to_number: str, from_number: Optional[str], metadata: Dict[str, Any]) -> str:
        """
        Start an outbound call using ElevenLabs SDK.
        
        Args:
            agent_id: ElevenLabs agent ID
            agent_phone_number_id: ElevenLabs agent phone number ID
            to_number: Destination phone number (E.164)
            from_number: Source phone number (optional)
            metadata: Agent metadata and configuration
            
        Returns:
            call_id for tracking
        """
        call_id = str(uuid.uuid4())

        config = get_config()
        service_cfg = getattr(config, "service", None)
        destination_number = to_number

        if service_cfg and service_cfg.force_test_call_number and service_cfg.test_call_number:
            original_tail = to_number[-4:] if to_number and len(to_number) > 4 else to_number
            override_tail = service_cfg.test_call_number[-4:] if len(service_cfg.test_call_number) > 4 else service_cfg.test_call_number
            self.logger._log_event(
                level="INFO",
                event_type="test_mode_override",
                message="Overriding destination number for testing",
                metadata={
                    "override_active": True,
                    "original_number_last4": original_tail,
                    "override_number_last4": override_tail,
                },
                correlation_id=call_id,
            )
            destination_number = service_cfg.test_call_number

        try:
            self.logger.log_call_attempt(call_id, destination_number, agent_id)

            # Import ElevenLabs SDK
            from elevenlabs.client import ElevenLabs
            from elevenlabs import UnauthorizedError, ForbiddenError, BadRequestError

            # Initialize client with API key
            client = ElevenLabs(api_key=config.elevenlabs.api_key)
            
            # Step 1: Verify agent exists and list available agents
            self.logger._log_event(
                level="DEBUG",
                event_type="agent_verification",
                message="Verifying agent exists before call",
                metadata={"agent_id": agent_id},
                correlation_id=call_id
            )
            
            try:
                agents_response = client.conversational_ai.agents.list()
                available_agents = {agent.agent_id: agent.name for agent in agents_response.agents}
                
                if agent_id not in available_agents:
                    error_msg = f"Agent {agent_id} not found in available agents: {list(available_agents.keys())}"
                    self.logger.log_call_initiation_failed(call_id, error_msg)
                    raise RuntimeError(error_msg)
                
                self.logger._log_event(
                    level="DEBUG",
                    event_type="agent_verified",
                    message="Agent verified successfully",
                    metadata={"agent_id": agent_id, "agent_name": available_agents[agent_id]},
                    correlation_id=call_id
                )
                
            except Exception as e:
                error_msg = f"Failed to verify agent: {str(e)}"
                self.logger.log_call_initiation_failed(call_id, error_msg)
                raise RuntimeError(error_msg)
            
            # Step 2: Assign the phone number to the specific agent
            self.logger._log_event(
                level="DEBUG",
                event_type="phone_number_assignment",
                message="Assigning phone number to agent",
                metadata={"agent_id": agent_id, "phone_number_id": agent_phone_number_id},
                correlation_id=call_id
            )
            
            try:
                phone_update_response = client.conversational_ai.phone_numbers.update(
                    phone_number_id=agent_phone_number_id,
                    agent_id=agent_id
                )
                
                self.logger._log_event(
                    level="DEBUG",
                    event_type="phone_number_assigned",
                    message="Phone number successfully assigned to agent",
                    metadata={
                        "agent_id": agent_id,
                        "phone_number_id": agent_phone_number_id,
                        "assigned_agent": phone_update_response.assigned_agent.agent_id if phone_update_response.assigned_agent else None
                    },
                    correlation_id=call_id
                )
                
            except Exception as e:
                error_msg = f"Failed to assign phone number to agent: {str(e)}"
                self.logger.log_call_initiation_failed(call_id, error_msg)
                raise RuntimeError(error_msg)
            
            # Extract dynamic variables and metadata
            dynamic_variables = metadata.get("prompt_variables", {})
            conversation_data = metadata.get("metadata", {})
            
            # Step 3: Combine conversation data with dynamic variables
            # According to ElevenLabs docs, dynamic variables should be passed in conversation_initiation_client_data
            full_conversation_data = {
                **conversation_data,
                "dynamic_variables": dynamic_variables
            }
            
            # Step 4: Make the actual outbound call using ElevenLabs SDK
            # Phone number is now assigned to the correct agent
            destination_number = "+4915117831779"  # For testing purposes; replace with destination_number in production
            call_response = client.conversational_ai.twilio.outbound_call(
                agent_id=agent_id,
                agent_phone_number_id=agent_phone_number_id,
                to_number=destination_number,
                conversation_initiation_client_data=full_conversation_data
            )
            
            # Extract the actual call ID from the response
            # According to ElevenLabs API docs, response has: success, message, conversation_id, callSid
            actual_call_id = getattr(call_response, 'callSid', None)
            if not actual_call_id:
                # Fallback to conversation_id if callSid is not available
                actual_call_id = getattr(call_response, 'conversation_id', call_id)
            
            # Log additional response details for debugging
            self.logger._log_event(
                level="DEBUG",
                event_type="elevenlabs_api_response",
                message="ElevenLabs API call successful",
                metadata={
                    "call_id": actual_call_id,
                    "agent_id": agent_id,
                    "agent_phone_number_id": agent_phone_number_id,
                    "to_number": "REDACTED",  # Don't log full phone numbers
                    "response_type": type(call_response).__name__,
                    "response_attributes": [attr for attr in dir(call_response) if not attr.startswith('_')],
                    "response_dict": call_response.__dict__ if hasattr(call_response, '__dict__') else "No __dict__",
                    "success": getattr(call_response, 'success', 'unknown'),
                    "message": getattr(call_response, 'message', 'unknown')
                },
                correlation_id=actual_call_id
            )
            
            self.logger.log_call_initiated(actual_call_id, destination_number)
            
            self.logger._log_event(
                level="INFO",
                event_type="call_flow_completed",
                message="Call flow completed successfully: agent verified, phone assigned, call initiated",
                metadata={
                    "call_id": actual_call_id,
                    "agent_id": agent_id,
                    "phone_number_id": agent_phone_number_id,
                    "to_number": "REDACTED"
                },
                correlation_id=actual_call_id
            )
            
            return actual_call_id
            
        except UnauthorizedError as e:
            error_msg = f"Authentication failed: {str(e)}"
            self.logger.log_call_initiation_failed(call_id, error_msg)
            raise RuntimeError(f"ElevenLabs authentication failed. Check your API key: {error_msg}")
            
        except ForbiddenError as e:
            error_msg = f"Forbidden: {str(e)}"
            self.logger.log_call_initiation_failed(call_id, error_msg)
            raise RuntimeError(f"ElevenLabs access forbidden: {error_msg}")
            
        except BadRequestError as e:
            error_msg = f"Bad request: {str(e)}"
            self.logger.log_call_initiation_failed(call_id, error_msg)
            raise RuntimeError(f"ElevenLabs bad request: {error_msg}")
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.log_call_initiation_failed(call_id, error_msg)
            raise RuntimeError(f"Failed to initiate call: {error_msg}")
    
    def store_call_info(self, call_id: str, idempotency_key: str, task: CallTask):
        """Store call tracking information."""
        call_info = {
            "call_id": call_id,
            "idempotency_key": idempotency_key,
            "task_id": task.task_id,
            "intent": task.intent.value,
            "business_phone": task.business.phone,
            "user_name": task.user.name,
            "started_at": datetime.utcnow(),
            "status": "initiated",
            "metadata": {
                "autonomy_level": task.policy.autonomy_level,
                "max_duration": task.policy.max_call_duration_minutes,
                "locale": task.locale
            }
        }
        
        self._active_calls[call_id] = call_info
        self.logger.log_call_stored(call_id, idempotency_key)
    
    def get_call_info(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve call information."""
        return self._active_calls.get(call_id)
    
    def complete_call(self, call_id: str, result: Dict[str, Any]):
        """Mark call as completed and move to history."""
        if call_id in self._active_calls:
            call_info = self._active_calls.pop(call_id)
            call_info.update({
                "completed_at": datetime.utcnow(),
                "status": "completed",
                "result": result
            })
            self._call_history[call_id] = call_info
            self.logger.log_call_completed(call_id)
    
    def fail_call(self, call_id: str, error: str):
        """Mark call as failed and move to history."""
        if call_id in self._active_calls:
            call_info = self._active_calls.pop(call_id)
            call_info.update({
                "completed_at": datetime.utcnow(),
                "status": "failed",
                "error": error
            })
            self._call_history[call_id] = call_info
            self.logger.log_call_failed(call_id, error)
    
    def get_active_calls(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active calls."""
        return self._active_calls.copy()
    
    def get_call_history(self) -> Dict[str, Dict[str, Any]]:
        """Get call history."""
        return self._call_history.copy()
    
    def cleanup_old_calls(self, max_age_hours: int = 24):
        """Clean up old completed calls from history."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for call_id, call_info in self._call_history.items():
            completed_at = call_info.get("completed_at")
            if completed_at and completed_at.timestamp() < cutoff_time:
                to_remove.append(call_id)
        
        for call_id in to_remove:
            del self._call_history[call_id]
        
        if to_remove:
            self.logger.log_calls_cleaned_up(len(to_remove))


# Global caller instance
caller = OutboundCaller()
