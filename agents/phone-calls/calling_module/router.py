"""
Public API router for the Calling Module.

Provides the main entry points that the supervisor agent calls.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
from threading import Lock

from .contracts import CallTask, CallResult, ValidationResult
from .input_adapter import InputAdapter
from .payload_builder import PayloadBuilder
from .outbound_caller import OutboundCaller
from .postcall_handler import PostCallHandler
from .observability import ObservabilityLogger


class CallingModuleRouter:
    """Main router for the calling module."""
    
    def __init__(self):
        self._input_adapter = None
        self._payload_builder = None
        self._outbound_caller = None
        self._postcall_handler = None
        self._logger = None
        self._pending_results: Dict[str, asyncio.Future] = {}
        self._completed_results: Dict[str, Dict[str, Any]] = {}
        self._pending_lock = Lock()
    
    @property
    def input_adapter(self):
        if self._input_adapter is None:
            self._input_adapter = InputAdapter()
        return self._input_adapter
    
    @property
    def payload_builder(self):
        if self._payload_builder is None:
            self._payload_builder = PayloadBuilder()
        return self._payload_builder
    
    @property
    def outbound_caller(self):
        if self._outbound_caller is None:
            self._outbound_caller = OutboundCaller()
        return self._outbound_caller
    
    @property
    def postcall_handler(self):
        if self._postcall_handler is None:
            self._postcall_handler = PostCallHandler()
        return self._postcall_handler
    
    @property
    def logger(self):
        if self._logger is None:
            self._logger = ObservabilityLogger()
        return self._logger
    
    def start_call(self, task_data: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> str:
        """
        Start an outbound call for the given task.
        
        Args:
            task_data: Raw task data from supervisor
            policy: Optional policy overrides
            
        Returns:
            call_id for tracking the call
            
        Raises:
            ValueError: If task validation fails
            RuntimeError: If call initiation fails
        """
        # Merge policy if provided
        if policy:
            task_data["policy"] = {**task_data.get("policy", {}), **policy}
        
        # Validate and normalize input
        self.logger.log_task_received(task_data)
        validation_result = self.input_adapter.validate(task_data)
        
        if not validation_result.is_valid:
            error_msg = f"Task validation failed: {[e.message for e in validation_result.errors]}"
            self.logger.log_validation_failed(validation_result.errors)
            raise ValueError(error_msg)
        
        normalized_task = validation_result.normalized_task
        
        # Build payload for agent
        payload = self.payload_builder.build(normalized_task)
        self.logger.log_payload_built(normalized_task.idempotency_key, payload)
        
        # Initiate outbound call
        try:
            # Combine metadata and prompt variables for the agent
            agent_context = {
                "metadata": payload["metadata"],
                "prompt_variables": payload["prompt_variables"]
            }
            
            call_id = self.outbound_caller.start_call(
                agent_id=payload["agent_id"],
                agent_phone_number_id=payload["agent_phone_number_id"],
                to_number=normalized_task.business.phone,
                from_number=payload.get("from_number"),
                metadata=agent_context
            )
            
            # Store call tracking info
            self.outbound_caller.store_call_info(
                call_id=call_id,
                idempotency_key=normalized_task.idempotency_key,
                task=normalized_task
            )
            
            self.logger.log_call_placed(call_id, normalized_task.idempotency_key)
            return call_id
            
        except Exception as e:
            self.logger.log_call_failed(normalized_task.idempotency_key, str(e))
            raise RuntimeError(f"Failed to initiate call: {str(e)}")
    
    def on_postcall(self, webhook_payload: Dict[str, Any]) -> CallResult:
        """
        Process post-call webhook from ElevenLabs.
        
        Args:
            webhook_payload: Raw webhook data from ElevenLabs
            
        Returns:
            Normalized CallResult for supervisor
        """
        self.logger.log_postcall_received(webhook_payload)
        
        try:
            result = self.postcall_handler.process_webhook(webhook_payload)
            self.logger.log_result_normalized(result)
            serialized = self.serialize_call_result(result)
            if serialized.get("call_id"):
                self.notify_call_result(serialized["call_id"], serialized)
            return result
        except Exception as e:
            self.logger.log_postcall_error(str(e))
            call_id = webhook_payload.get("call_id") or webhook_payload.get("conversation_id")
            if call_id:
                self.notify_call_error(call_id, RuntimeError(f"Failed to process post-call webhook: {str(e)}"))
            raise RuntimeError(f"Failed to process post-call webhook: {str(e)}")

    def serialize_call_result(self, result: CallResult) -> Dict[str, Any]:
        """Convert CallResult to dict for API responses."""
        result_dict: Dict[str, Any] = {
            "status": result.status.value,
            "message": result.message,
            "next_action": result.next_action.value,
            "call_id": result.call_id,
            "task_id": result.task_id,
            "idempotency_key": result.idempotency_key,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "transcript": result.transcript
        }

        if result.core_artifact:
            result_dict["core_artifact"] = {
                "booking_reference": result.core_artifact.booking_reference,
                "confirmed_date": result.core_artifact.confirmed_date.isoformat() if result.core_artifact.confirmed_date else None,
                "confirmed_time": result.core_artifact.confirmed_time.isoformat() if result.core_artifact.confirmed_time else None,
                "party_size": result.core_artifact.party_size,
                "total_cost": result.core_artifact.total_cost,
                "confirmation_code": result.core_artifact.confirmation_code,
                "special_instructions": result.core_artifact.special_instructions
            }

        if result.observations:
            result_dict["observations"] = {
                "offered_alternatives": result.observations.offered_alternatives,
                "online_booking_hints": result.observations.online_booking_hints,
                "business_hours": result.observations.business_hours,
                "cancellation_policy": result.observations.cancellation_policy,
                "payment_methods": result.observations.payment_methods,
                "policies_mentioned": result.observations.policies_mentioned
            }

        if result.evidence:
            result_dict["evidence"] = {
                "provider_call_id": result.evidence.provider_call_id,
                "call_duration_seconds": result.evidence.call_duration_seconds,
                "transcript_url": result.evidence.transcript_url,
                "recording_url": result.evidence.recording_url
            }

        return result_dict

    async def wait_for_result(self, call_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for post-call result corresponding to call_id."""
        loop = asyncio.get_running_loop()
        future = self._get_or_create_future(call_id, loop)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            with self._pending_lock:
                self._pending_results.pop(call_id, None)
            raise

    def notify_call_result(self, call_id: str, result: Dict[str, Any]):
        """Resolve pending waiter with successful result."""
        if not call_id:
            return
        with self._pending_lock:
            future = self._pending_results.pop(call_id, None)
            if future is not None:
                loop = future.get_loop()

                def _set_result():
                    if not future.done():
                        future.set_result(result)

                if loop.is_running():
                    loop.call_soon_threadsafe(_set_result)
                else:
                    _set_result()
            else:
                self._completed_results[call_id] = result

    def notify_call_error(self, call_id: str, error: Exception):
        """Resolve pending waiter with an error."""
        if not call_id:
            return
        with self._pending_lock:
            future = self._pending_results.pop(call_id, None)
            if future is not None:
                loop = future.get_loop()

                def _set_exception():
                    if not future.done():
                        future.set_exception(error)

                if loop.is_running():
                    loop.call_soon_threadsafe(_set_exception)
                else:
                    _set_exception()
            else:
                self._completed_results[call_id] = error

    def _get_or_create_future(self, call_id: str, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        with self._pending_lock:
            if call_id in self._completed_results:
                stored = self._completed_results.pop(call_id)
                future = loop.create_future()
                if isinstance(stored, Exception):
                    future.set_exception(stored)
                else:
                    future.set_result(stored)
                return future

            future = self._pending_results.get(call_id)
            if future is None or future.done():
                future = loop.create_future()
                self._pending_results[call_id] = future
            return future


# Global router instance
router = CallingModuleRouter()


# Convenience functions for external use
def start_call(task_data: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> str:
    """Start an outbound call for the given task."""
    return router.start_call(task_data, policy)


def on_postcall(webhook_payload: Dict[str, Any]) -> CallResult:
    """Process post-call webhook from ElevenLabs."""
    return router.on_postcall(webhook_payload)
