"""
Calling Module for Jarvis Multi-Agent System

This module enables outbound phone calls to businesses on behalf of users
for tasks like reservations, scheduling, cancellations, and availability checks.
"""

__version__ = "0.1.0"
__author__ = "Jarvis Team"

from .router import start_call, on_postcall, router
from .contracts import (
    CallTask, CallPolicy, CallResult, 
    ReservationTask, RescheduleTask, CancelTask, InfoTask
)

async def wait_for_call_result(call_id: str, timeout: float | None = None):
    """Wait for the post-call result associated with call_id."""
    return await router.wait_for_result(call_id, timeout)


def serialize_call_result(result: CallResult) -> dict:
    """Serialize CallResult into API-ready dict."""
    return router.serialize_call_result(result)


def notify_call_result(call_id: str, result: dict):
    """Notify the router that a call result is available."""
    router.notify_call_result(call_id, result)


def notify_call_error(call_id: str, error: Exception):
    """Notify the router that a call resulted in error."""
    router.notify_call_error(call_id, error)

__all__ = [
    "start_call",
    "on_postcall", 
    "wait_for_call_result",
    "serialize_call_result",
    "notify_call_result",
    "notify_call_error",
    "CallTask",
    "CallPolicy",
    "CallResult",
    "ReservationTask",
    "RescheduleTask", 
    "CancelTask",
    "InfoTask"
]
