"""
Calling Module for Jarvis Multi-Agent System

This module enables outbound phone calls to businesses on behalf of users
for tasks like reservations, scheduling, cancellations, and availability checks.
"""

__version__ = "0.1.0"
__author__ = "Jarvis Team"

from .router import start_call, on_postcall
from .contracts import (
    CallTask, CallPolicy, CallResult, 
    ReservationTask, RescheduleTask, CancelTask, InfoTask
)

__all__ = [
    "start_call",
    "on_postcall", 
    "CallTask",
    "CallPolicy",
    "CallResult",
    "ReservationTask",
    "RescheduleTask", 
    "CancelTask",
    "InfoTask"
]
