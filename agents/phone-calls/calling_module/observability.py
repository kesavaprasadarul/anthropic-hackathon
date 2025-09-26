"""
Observability and logging for the Calling Module.

Provides structured logging, metrics, and monitoring capabilities.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .contracts import CallResult, ValidationError


@dataclass
class LogEvent:
    """Structured log event."""
    timestamp: str
    level: str
    event_type: str
    message: str
    metadata: Dict[str, Any]
    correlation_id: Optional[str] = None


@dataclass
class Metric:
    """Structured metric."""
    name: str
    value: float
    timestamp: str
    tags: Dict[str, str]
    unit: Optional[str] = None


class ObservabilityLogger:
    """Handles structured logging and metrics collection."""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics: List[Metric] = []
    
    def log_task_received(self, task_data: Dict[str, Any]):
        """Log when a task is received."""
        self._log_event(
            level="INFO",
            event_type="task_received",
            message="Call task received from supervisor",
            metadata={
                "intent": task_data.get("intent"),
                "business_phone": task_data.get("business", {}).get("phone", "REDACTED"),
                "user_name": task_data.get("user", {}).get("name", "REDACTED"),
                "locale": task_data.get("locale", "en-US")
            }
        )
    
    def log_validation_failed(self, errors: List[ValidationError]):
        """Log validation failures."""
        self._log_event(
            level="WARN",
            event_type="validation_failed",
            message=f"Task validation failed with {len(errors)} errors",
            metadata={
                "error_count": len(errors),
                "errors": [{"field": e.field, "message": e.message} for e in errors]
            }
        )
        self._record_metric("validation_failures", 1, {"type": "input_validation"})
    
    def log_payload_built(self, idempotency_key: str, payload: Dict[str, Any]):
        """Log when payload is built for agent."""
        self._log_event(
            level="INFO",
            event_type="payload_built",
            message="Agent payload built successfully",
            metadata={
                "idempotency_key": idempotency_key,
                "agent_id": payload.get("agent_id"),
                "voice_id": payload.get("voice_id"),
                "language": payload.get("language")
            },
            correlation_id=idempotency_key
        )
    
    def log_call_attempt(self, call_id: str, to_number: str, agent_id: str):
        """Log call initiation attempt."""
        self._log_event(
            level="INFO",
            event_type="call_attempt",
            message="Attempting to initiate outbound call",
            metadata={
                "call_id": call_id,
                "to_number": "REDACTED",  # Don't log full phone numbers
                "agent_id": agent_id
            },
            correlation_id=call_id
        )
    
    def log_call_initiated(self, call_id: str, to_number: str):
        """Log successful call initiation."""
        self._log_event(
            level="INFO",
            event_type="call_initiated",
            message="Outbound call initiated successfully",
            metadata={
                "call_id": call_id,
                "to_number": "REDACTED"
            },
            correlation_id=call_id
        )
        self._record_metric("calls_initiated", 1, {"status": "success"})
    
    def log_call_initiation_failed(self, call_id: str, error: str):
        """Log call initiation failure."""
        self._log_event(
            level="ERROR",
            event_type="call_initiation_failed",
            message=f"Failed to initiate call: {error}",
            metadata={
                "call_id": call_id,
                "error": error
            },
            correlation_id=call_id
        )
        self._record_metric("calls_initiated", 1, {"status": "failed"})
    
    def log_call_placed(self, call_id: str, idempotency_key: str):
        """Log when call is placed."""
        self._log_event(
            level="INFO",
            event_type="call_placed",
            message="Call placed successfully",
            metadata={
                "call_id": call_id,
                "idempotency_key": idempotency_key
            },
            correlation_id=call_id
        )
        self._record_metric("calls_placed", 1)
    
    def log_call_failed(self, idempotency_key: str, error: str):
        """Log call failure."""
        self._log_event(
            level="ERROR",
            event_type="call_failed",
            message=f"Call failed: {error}",
            metadata={
                "idempotency_key": idempotency_key,
                "error": error
            },
            correlation_id=idempotency_key
        )
        self._record_metric("calls_failed", 1)
    
    def log_call_stored(self, call_id: str, idempotency_key: str):
        """Log call storage."""
        self._log_event(
            level="DEBUG",
            event_type="call_stored",
            message="Call information stored for tracking",
            metadata={
                "call_id": call_id,
                "idempotency_key": idempotency_key
            },
            correlation_id=call_id
        )
    
    def log_call_completed(self, call_id: str):
        """Log call completion."""
        self._log_event(
            level="INFO",
            event_type="call_completed",
            message="Call completed successfully",
            metadata={"call_id": call_id},
            correlation_id=call_id
        )
        self._record_metric("calls_completed", 1)
    
    def log_postcall_received(self, webhook_payload: Dict[str, Any]):
        """Log post-call webhook received."""
        self._log_event(
            level="INFO",
            event_type="postcall_received",
            message="Post-call webhook received",
            metadata={
                "call_id": webhook_payload.get("call_id"),
                "status": webhook_payload.get("status"),
                "has_transcript": bool(webhook_payload.get("transcript")),
                "has_summary": bool(webhook_payload.get("summary"))
            },
            correlation_id=webhook_payload.get("call_id")
        )
    
    def log_webhook_processing_started(self, webhook_payload: Dict[str, Any]):
        """Log webhook processing start."""
        self._log_event(
            level="DEBUG",
            event_type="webhook_processing_started",
            message="Started processing post-call webhook",
            metadata={
                "call_id": webhook_payload.get("call_id"),
                "payload_keys": list(webhook_payload.keys())
            },
            correlation_id=webhook_payload.get("call_id")
        )
    
    def log_webhook_processing_completed(self, result: CallResult):
        """Log webhook processing completion."""
        self._log_event(
            level="INFO",
            event_type="webhook_processing_completed",
            message=f"Webhook processing completed with status: {result.status.value}",
            metadata={
                "call_id": result.call_id,
                "status": result.status.value,
                "next_action": result.next_action.value,
                "has_artifact": bool(result.core_artifact),
                "has_observations": bool(result.observations)
            },
            correlation_id=result.call_id
        )
        self._record_metric("webhook_processing_completed", 1, {"status": result.status.value})
    
    def log_webhook_processing_error(self, error: str):
        """Log webhook processing error."""
        self._log_event(
            level="ERROR",
            event_type="webhook_processing_error",
            message=f"Webhook processing failed: {error}",
            metadata={"error": error}
        )
        self._record_metric("webhook_processing_errors", 1)
    
    def log_postcall_error(self, error: str):
        """Log post-call processing error."""
        self._log_event(
            level="ERROR",
            event_type="postcall_error",
            message=f"Post-call processing failed: {error}",
            metadata={"error": error}
        )
        self._record_metric("postcall_errors", 1)
    
    def log_result_normalized(self, result: CallResult):
        """Log result normalization."""
        self._log_event(
            level="INFO",
            event_type="result_normalized",
            message=f"Call result normalized: {result.status.value}",
            metadata={
                "call_id": result.call_id,
                "task_id": result.task_id,
                "idempotency_key": result.idempotency_key,
                "status": result.status.value,
                "next_action": result.next_action.value,
                "message": result.message
            },
            correlation_id=result.call_id
        )
        self._record_metric("results_normalized", 1, {"status": result.status.value})
    
    def log_calls_cleaned_up(self, count: int):
        """Log call cleanup."""
        self._log_event(
            level="INFO",
            event_type="calls_cleaned_up",
            message=f"Cleaned up {count} old call records",
            metadata={"cleaned_count": count}
        )
    
    def _log_event(self, level: str, event_type: str, message: str, 
                   metadata: Dict[str, Any], correlation_id: Optional[str] = None):
        """Log a structured event."""
        event = LogEvent(
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            event_type=event_type,
            message=message,
            metadata=metadata,
            correlation_id=correlation_id
        )
        
        # Print as JSON for structured logging
        print(json.dumps(asdict(event), default=str))
    
    def _record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric."""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.utcnow().isoformat(),
            tags=tags or {}
        )
        self.metrics.append(metric)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of collected metrics."""
        summary = {}
        
        # Group metrics by name
        metric_groups = {}
        for metric in self.metrics:
            if metric.name not in metric_groups:
                metric_groups[metric.name] = []
            metric_groups[metric.name].append(metric)
        
        # Calculate summaries
        for name, metrics in metric_groups.items():
            values = [m.value for m in metrics]
            summary[name] = {
                "count": len(values),
                "total": sum(values),
                "average": sum(values) / len(values) if values else 0
            }
        
        # Add uptime
        uptime_seconds = time.time() - self.start_time
        summary["uptime_seconds"] = uptime_seconds
        
        return summary
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log events (for debugging)."""
        # In a real implementation, this would query a log store
        # For now, return empty list as we're just printing logs
        return []
