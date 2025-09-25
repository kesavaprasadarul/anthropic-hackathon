"""
Public API router for the Calling Module.

Provides the main entry points that the supervisor agent calls.
"""

from typing import Optional, Dict, Any
from datetime import datetime

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
            return result
        except Exception as e:
            self.logger.log_postcall_error(str(e))
            raise RuntimeError(f"Failed to process post-call webhook: {str(e)}")


# Global router instance
router = CallingModuleRouter()


# Convenience functions for external use
def start_call(task_data: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> str:
    """Start an outbound call for the given task."""
    return router.start_call(task_data, policy)


def on_postcall(webhook_payload: Dict[str, Any]) -> CallResult:
    """Process post-call webhook from ElevenLabs."""
    return router.on_postcall(webhook_payload)
