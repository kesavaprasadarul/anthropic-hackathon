"""
Data contracts for the Calling Module.

Defines input/output structures for tasks, policies, and results.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, List, Dict, Any, Literal
from enum import Enum


class TaskIntent(Enum):
    """Supported task intents."""
    RESERVE = "reserve"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    INFO = "info"


class CallStatus(Enum):
    """Standardized call outcome status."""
    COMPLETED = "completed"
    NO_AVAILABILITY = "no_availability"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    IVR_BLOCKED = "ivr_blocked"
    NEEDS_USER_INPUT = "needs_user_input"
    TIMEOUT = "timeout"
    ERROR = "error"


class NextAction(Enum):
    """Recommended next actions."""
    ADD_TO_CALENDAR = "add_to_calendar"
    RETRY_LATER = "retry_later"
    REQUEST_USER_INPUT = "request_user_input"
    SWITCH_CHANNEL = "switch_channel"
    NONE = "none"


@dataclass
class BusinessInfo:
    """Target business information."""
    phone: str  # E.164 format
    name: str
    timezone: str = "UTC"
    website: Optional[str] = None
    address: Optional[str] = None


@dataclass
class UserInfo:
    """Acting user information."""
    name: str
    callback_phone: Optional[str] = None  # E.164 format
    email: Optional[str] = None  # Only if policy allows


@dataclass
class CallPolicy:
    """Call execution policy and constraints."""
    autonomy_level: Literal["low", "medium", "high"] = "medium"
    max_call_duration_minutes: int = 4
    allow_payment_info: bool = False
    allow_personal_details: bool = True
    disclosure_allowlist: List[str] = field(default_factory=list)
    max_retries: int = 2


@dataclass
class TimeWindow:
    """Time window specification."""
    start_time: time  # 24h format
    end_time: time    # 24h format
    date: Optional[datetime] = None  # For specific date reservations


@dataclass
class ReservationTask:
    """Reservation/scheduling task details."""
    date: datetime
    time_window: TimeWindow
    party_size: int
    notes: Optional[str] = None
    budget_range: Optional[str] = None  # e.g., "$20-40"
    special_requests: Optional[str] = None


@dataclass
class RescheduleTask:
    """Reschedule task details."""
    new_date: datetime
    new_time_window: TimeWindow
    booking_reference: Optional[str] = None
    disambiguation_bundle: Optional[Dict[str, Any]] = None  # Name, date, time, etc.


@dataclass
class CancelTask:
    """Cancellation task details."""
    booking_reference: Optional[str] = None
    disambiguation_bundle: Optional[Dict[str, Any]] = None
    name_on_reservation: Optional[str] = None
    cancellation_reason: Optional[str] = None


@dataclass
class InfoTask:
    """Information request task details."""
    question_type: Literal["availability", "status", "hours", "price", "policies"]
    context: Optional[str] = None
    specific_date: Optional[datetime] = None
    party_size: Optional[int] = None


@dataclass
class CallTask:
    """Complete call task specification."""
    # Envelope information
    business: BusinessInfo
    user: UserInfo
    intent: TaskIntent
    locale: str = "en-US"
    policy: CallPolicy = field(default_factory=CallPolicy)
    
    # Task-specific payload
    reservation: Optional[ReservationTask] = None
    reschedule: Optional[RescheduleTask] = None
    cancel: Optional[CancelTask] = None
    info: Optional[InfoTask] = None
    
    # Metadata
    idempotency_key: Optional[str] = None
    task_id: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class CallArtifact:
    """Core artifact from successful call."""
    booking_reference: Optional[str] = None
    confirmed_date: Optional[datetime] = None
    confirmed_time: Optional[time] = None
    party_size: Optional[int] = None
    total_cost: Optional[str] = None
    special_instructions: Optional[str] = None
    confirmation_code: Optional[str] = None


@dataclass
class CallObservations:
    """Observations and additional information from call."""
    offered_alternatives: List[str] = field(default_factory=list)
    online_booking_hints: List[str] = field(default_factory=list)
    policies_mentioned: List[str] = field(default_factory=list)
    business_hours: Optional[str] = None
    cancellation_policy: Optional[str] = None
    payment_methods: List[str] = field(default_factory=list)


@dataclass
class CallEvidence:
    """Evidence and references from the call."""
    provider_call_id: Optional[str] = None
    transcript_url: Optional[str] = None
    recording_url: Optional[str] = None
    call_duration_seconds: Optional[int] = None
    webhook_payload: Optional[Dict[str, Any]] = None


@dataclass
class CallResult:
    """Normalized call outcome."""
    status: CallStatus
    core_artifact: Optional[CallArtifact] = None
    observations: Optional[CallObservations] = None
    next_action: NextAction = NextAction.NONE
    evidence: Optional[CallEvidence] = None
    message: str = ""
    
    # Metadata
    call_id: Optional[str] = None
    task_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass
class ValidationError:
    """Input validation error details."""
    field: str
    message: str
    required_for_intent: TaskIntent


@dataclass
class ValidationResult:
    """Input validation result."""
    is_valid: bool
    normalized_task: Optional[CallTask] = None
    errors: List[ValidationError] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
