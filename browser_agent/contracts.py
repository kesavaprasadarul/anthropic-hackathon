"""
Data contracts and interfaces for the Browser Automation Module.

This module defines all data structures, enums, and interfaces used throughout
the browser automation system for reservations and information requests.
"""

from datetime import date, time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Union, Any, Protocol
from pydantic import BaseModel, Field, ConfigDict


# Core Enums
class Intent(str, Enum):
    """Intent types for browser automation tasks."""
    RESERVE = "reserve"
    INFO = "info"
    RECOMMEND = "recommend"


class Status(str, Enum):
    """Standardized status vocabulary for browser automation outcomes."""
    COMPLETED = "completed"
    NO_AVAILABILITY = "no_availability"
    NO_WEBSITE = "no_website"
    RESTAURANT_CLOSED = "restaurant_closed"
    NEEDS_USER_INPUT = "needs_user_input"
    TIMEOUT = "timeout"
    ERROR = "error"


class InfoType(str, Enum):
    """Types of information that can be requested."""
    OPENING_HOURS = "opening_hours"
    PRICING = "pricing"
    DIETARY_INFORMATION = "dietary_information"
    AVAILABILITY = "availability"


class NextAction(str, Enum):
    """Suggested next actions based on automation outcome."""
    ADD_TO_CALENDAR = "add_to_calendar"
    RETRY_LATER = "retry_later" 
    REQUEST_USER_INPUT = "request_user_input"
    SWITCH_CHANNEL = "switch_channel"
    NONE = "none"


class SeatingPreference(str, Enum):
    """Seating preference options."""
    OUTSIDE = "outside"
    INSIDE = "inside"


# Business and User Models
class TargetBusiness(BaseModel):
    """Business information for automation target."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    name: str
    website: str
    phone: Optional[str] = None
    timezone: Optional[str] = None


class User(BaseModel):
    """User information for the automation request."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


# Task Payload Models
class ReservePayload(BaseModel):
    """Payload for reservation requests."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    date: date
    time_window_start: time
    time_window_end: time
    party_size: int
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None  # allergies, seating, etc.
    budget: Optional[float] = None


class InfoPayload(BaseModel):
    """Payload for information requests."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    info_type: InfoType
    context_date: Optional[date] = None
    context_time: Optional[time] = None

class RecommendPayload(BaseModel):
    """Payload for information requests."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})

    user_query: str
    area: str
    budget: int


# Policy and Configuration
class Policy(BaseModel):
    """Automation policy configuration."""
    autonomy_level: str = "medium"  # low, medium, high
    max_steps: int = 50
    take_screenshots: bool = True
    use_vision: bool = True
    max_failures: int = 3


# Main Task Model
class BrowserTask(BaseModel):
    """Complete browser automation task specification."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    business: TargetBusiness
    user: User
    intent: Intent
    payload: Union[ReservePayload, InfoPayload, RecommendPayload]
    policy: Policy = Field(default_factory=Policy)
    locale: str = "en-US"
    idempotency_key: Optional[str] = None


# Output Artifacts
class BookingDetails(BaseModel):
    """Structured booking confirmation details."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    booking_reference: Optional[str] = None
    confirmed_date: date
    confirmed_time: time
    party_size: int
    customer_name: str
    restaurant_name: str
    special_requests: Optional[str] = None

class InfoResponse(BaseModel):
    """Structured information response."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    info_type: InfoType
    data: Any  # The actual information content
    additional_notes: Optional[str] = None
    source_url: Optional[str] = None

class RecommendResponse(BaseModel):
    """Structured information response."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    info_type: InfoType
    data: Any  # The actual information content
    additional_notes: Optional[str] = None
    source_url: Optional[str] = None


# Evidence and Observability
class Evidence(BaseModel):
    """Evidence collected during browser automation."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    screenshots: List[str] = Field(default_factory=list)  # paths or base64 encoded
    browsing_summary: str
    steps_taken: int = 0
    duration_seconds: Optional[float] = None


# Final Result Model
class BrowserAutomationResult(BaseModel):
    """Standardized result from browser automation."""
    model_config = ConfigDict(json_encoders={date: lambda v: v.isoformat(), time: lambda v: v.isoformat()})
    
    status: Status
    message: str
    next_action: NextAction = NextAction.NONE
    core_artifact: Optional[Union[BookingDetails, InfoResponse]] = None
    evidence: Evidence
    error_reason: Optional[str] = None
    missing_fields: Optional[List[str]] = None


# Protocol Interfaces
class BrowserExecutor(Protocol):
    """Interface for browser automation executors."""
    
    async def execute(self, task: BrowserTask) -> BrowserAutomationResult:
        """Execute a browser automation task."""
        ...


class InputValidator(Protocol):
    """Interface for input validation."""
    
    def validate_task(self, task_data: dict) -> BrowserTask:
        """Validate and normalize input task data."""
        ...


class ResultProcessor(Protocol):
    """Interface for result processing."""
    
    def process_result(self, raw_result: Any, task: BrowserTask) -> BrowserAutomationResult:
        """Process raw browser automation results into standardized format."""
        ...