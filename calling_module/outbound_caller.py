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
        
        try:
            self.logger.log_call_attempt(call_id, to_number, agent_id)
            
            # Import ElevenLabs SDK
            from elevenlabs.client import ElevenLabs
            from elevenlabs import UnauthorizedError, ForbiddenError, BadRequestError
            
            # Initialize client with API key
            client = ElevenLabs(api_key=get_config().elevenlabs.api_key)
            
            # Make the actual outbound call using ElevenLabs SDK
            call_response = client.conversational_ai.twilio.outbound_call(
                agent_id=agent_id,
                agent_phone_number_id=agent_phone_number_id,
                to_number=to_number,
                conversation_initiation_client_data=metadata
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
            
            self.logger.log_call_initiated(actual_call_id, to_number)
            
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
