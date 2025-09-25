import asyncio
from datetime import date, time
from enum import Enum
from typing import Optional, List, Union, Any
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, ChatGoogle
from pydantic import BaseModel, Field

# Enums
class Intent(str, Enum):
    RESERVE = "reserve"
    INFO = "info"

class Status(str, Enum):
    COMPLETED = "completed"
    NO_AVAILABILITY = "no_availability"
    NO_WEBSITE = "no_website"
    RESTAURANT_CLOSED = "restaurant_closed"
    NEEDS_USER_INPUT = "needs_user_input"
    TIMEOUT = "timeout"
    ERROR = "error"

class InfoType(str, Enum):
    OPENING_HOURS = "opening_hours"
    PRICING = "pricing"
    DIETARY_INFORMATION = "dietary_information"
    AVAILABILITY = "availability"

class SeatingPreference(str, Enum):
    OUTSIDE = "outside"
    INSIDE = "inside"

# Input Models
class TargetBusiness(BaseModel):
    name: str
    website: str

class ReservePayload(BaseModel):
    name: str  # Name for the reservation
    date: date
    time_window_start: time
    time_window_end: time
    email: Optional[str] = None
    phone_number: Optional[str] = None
    party_size: int
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None  # allergies, seating, etc.
    budget: Optional[float] = None

class InfoPayload(BaseModel):
    info_type: InfoType
    context_date: Optional[date] = None
    context_time: Optional[time] = None

class Envelope(BaseModel):
    target_business: TargetBusiness
    intent: Intent
    intent_payload: Union[ReservePayload, InfoPayload]
    # idempotency_key: Optional[str] = None
    # callback_endpoint: Optional[str] = None

# Output Models
class BookingDetails(BaseModel):
    who: str  # customer name/contact
    when: date
    time: time
    where: str  # restaurant name and location
    size: int  # party size
    confirmation_number: Optional[str] = None
    special_requests: Optional[str] = None

class InfoResponse(BaseModel):
    info_type: InfoType
    data: Any  # flexible field for different info types
    additional_notes: Optional[str] = None

class Evidence(BaseModel):
    screenshots: List[str] = Field(default_factory=list)  # paths or base64 encoded
    browsing_summary: str

class BrowserAgentResult(BaseModel):
    status: Status
    artifact: Optional[Union[BookingDetails, InfoResponse]] = None
    evidence: Evidence
    error_reason: Optional[str] = None  # only if not completed
    missing_fields: Optional[List[str]] = None  # specific missing info

class BrowserAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = ChatGoogle(model=model_name)
    
    async def process(self, envelope: Envelope) -> BrowserAgentResult:
        """Main entry point for processing browser automation requests"""
        try:
            if envelope.intent == Intent.RESERVE:
                return await self._handle_reservation(envelope)
            elif envelope.intent == Intent.INFO:
                return await self._handle_info_request(envelope)
            else:
                return BrowserAgentResult(
                    status=Status.ERROR,
                    evidence=Evidence(browsing_summary="Invalid intent provided"),
                    error_reason="Invalid intent type"
                )
        except Exception as e:
            return BrowserAgentResult(
                status=Status.ERROR,
                evidence=Evidence(browsing_summary=f"Unexpected error: {str(e)}"),
                error_reason=f"System error: {str(e)}"
            )

    async def _handle_reservation(self, envelope: Envelope) -> BrowserAgentResult:
        """Handle reservation requests"""
        payload = envelope.intent_payload
        business = envelope.target_business
        
        # Validate required fields
        missing_fields = []
        if not payload.name or payload.name.strip() == "":
            missing_fields.append("name")
        if not payload.email and not payload.phone_number:
            missing_fields.append("email or phone_number")
        if not payload.party_size or payload.party_size < 1:
            missing_fields.append("party_size")
        
        if missing_fields:
            return BrowserAgentResult(
                status=Status.NEEDS_USER_INPUT,
                evidence=Evidence(browsing_summary="Missing required reservation information"),
                error_reason="Missing critical reservation details",
                missing_fields=missing_fields
            )

        task = f"""
        Make a restaurant reservation at {business.name} ({business.website})

        **Critical Instructions:**
        - Navigate to {business.website} and verify it's the correct restaurant
        - Check if restaurant is open on {payload.date} during {payload.time_window_start}-{payload.time_window_end}
        - Look for online reservation system (booking form, OpenTable, Resy, etc.)
        - If the website explicitly states that no reservations are possible or only via telefon, abort the process and format the output
        - Fill out reservation form with provided details
        - If the website does not provide a reservation system, search up the resetaurant on OpenTable and setup the reservation there. Do not use a website other than OpenTable. If you cannot find the website on OpenTable, abort the process.
        - Take screenshots at key steps for evidence
        - If any step fails, provide specific error details

        **Reservation Details:**
        - Name: {payload.name}
        - Date: {payload.date}
        - Time Window: {payload.time_window_start} - {payload.time_window_end}
        - Party Size: {payload.party_size}
        - Contact: {payload.email or payload.phone_number}
        {f"- Special Requests: {payload.notes}" if payload.notes else ""}
        {f"- Preferences: {payload.preferences}" if payload.preferences else ""}
        {f"- Duration: {payload.duration_minutes} minutes" if payload.duration_minutes else ""}

        **Return JSON with:**
        - success: boolean
        - confirmation_details: reservation confirmation info
        - error_type: if failed (NO_WEBSITE, RESTAURANT_CLOSED, NO_AVAILABILITY, etc.)
        - screenshots_taken: list of screenshot descriptions
        """

        agent = Agent(
            task=task,
            llm=self.model,
            use_vision=True,
            max_failures=3,
            generate_gif=False,
        )

        try:
            history = await agent.run(max_steps=50)
            
            result = history.final_result()
            
            # Parse agent result and convert to our format
            return self._parse_reservation_result(result, business, payload)
            
        except Exception as e:
            if "timeout" in str(e).lower():
                return BrowserAgentResult(
                    status=Status.TIMEOUT,
                    evidence=Evidence(browsing_summary="Agent execution exceeded time limits"),
                    error_reason="Process timed out"
                )
            else:
                return BrowserAgentResult(
                    status=Status.ERROR,
                    evidence=Evidence(browsing_summary=f"Agent execution failed: {str(e)}"),
                    error_reason=f"Execution error: {str(e)}"
                )

    async def _handle_info_request(self, envelope: Envelope) -> BrowserAgentResult:
        """Handle information requests"""
        payload = envelope.intent_payload
        business = envelope.target_business

        task = f"""
        Get {payload.info_type.value} information from {business.name} ({business.website})

        **Instructions:**
        - Navigate to {business.website}
        - Find information about {payload.info_type.value}
        {f"- Context: Check for {payload.context_date}" if payload.context_date else ""}
        {f"- Time context: {payload.context_time}" if payload.context_time else ""}
        - Take screenshots of relevant information
        - Extract and format the requested information clearly
        """

        agent = Agent(
            task=task,
            llm=self.model,
            use_vision=True,
            max_failures=3,
            generate_gif=False,
        )

        try:
            history = await agent.run(max_steps=30)            
            return BrowserAgentResult(
                status=Status.COMPLETED,
                artifact=InfoResponse(
                    info_type=payload.info_type.value,
                    data=history.final_result(),
                    additional_notes=""
                ),
                evidence=Evidence(screenshots=[],browsing_summary="")
            )
            
        except Exception as e:
            if "timeout" in str(e).lower():
                return BrowserAgentResult(
                    status=Status.TIMEOUT,
                    evidence=Evidence(browsing_summary="Agent execution exceeded time limits"),
                    error_reason="Process timed out"
                )
            else:
                return BrowserAgentResult(
                    status=Status.ERROR,
                    evidence=Evidence(browsing_summary=f"Agent execution failed: {str(e)}"),
                    error_reason=f"Execution error: {str(e)}"
                )

    def _parse_reservation_result(self, agent_result: Any, business: TargetBusiness, payload: ReservePayload) -> BrowserAgentResult:
        """Parse agent result for reservation requests"""
        # This would need to be implemented based on the actual format returned by the browser-use agent
        # For now, providing a template structure
        
        evidence = Evidence(
            screenshots=[],  # Would be populated from agent result
            browsing_summary="Reservation attempt completed"
        )

        if agent_result and "success" in str(agent_result) and "true" in str(agent_result).lower():
            booking = BookingDetails(
                who=payload.name,
                when=payload.date,
                time=payload.time_window_start,
                where=business.name,
                size=payload.party_size,
                special_requests=payload.notes
            )
            return BrowserAgentResult(
                status=Status.COMPLETED,
                artifact=booking,
                evidence=evidence
            )
        else:
            # Parse specific error types from agent result
            error_msg = str(agent_result) if agent_result else "Unknown error"
            
            if "no_website" in error_msg.lower():
                status = Status.NO_WEBSITE
            elif "closed" in error_msg.lower():
                status = Status.RESTAURANT_CLOSED
            elif "no_availability" in error_msg.lower():
                status = Status.NO_AVAILABILITY
            else:
                status = Status.ERROR
            
            return BrowserAgentResult(
                status=status,
                evidence=evidence,
                error_reason=error_msg
            )

    def _parse_info_result(self, agent_result: Any, info_type: InfoType) -> BrowserAgentResult:
        """Parse agent result for info requests"""
        evidence = Evidence(
            screenshots=[],  # Would be populated from agent result
            browsing_summary="Information request completed"
        )

        if agent_result and "info_found" in str(agent_result) and "true" in str(agent_result).lower():
            info_response = InfoResponse(
                info_type=info_type,
                data=agent_result  # Would extract specific data based on info_type
            )
            return BrowserAgentResult(
                status=Status.COMPLETED,
                artifact=info_response,
                evidence=evidence
            )
        else:
            return BrowserAgentResult(
                status=Status.NO_WEBSITE,
                evidence=evidence,
                error_reason="Could not find requested information"
            )

# Convenience function for backward compatibility and easy usage
async def process_browser_request(envelope: Envelope) -> BrowserAgentResult:
    """Convenience function to process a browser automation request"""
    agent = BrowserAgent()
    return await agent.process(envelope)

