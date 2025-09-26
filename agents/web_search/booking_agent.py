import re
import os
import json
from typing import List, Dict, Any, Optional

from smolagents import Tool, CodeAgent
from smolagents.models import LiteLLMModel

from ..contracts import AgentOutput
from .tools import GoogleCalendarCreateEventTool, GoogleCalendarAvailabilityTool
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

_FENCE_RE = re.compile(r'^```(?:json)?\s*\r?\n(.*)\r?\n```$', re.IGNORECASE | re.DOTALL)

def _strip_fences(s: str) -> str:
    m = _FENCE_RE.match(s.strip())
    return m.group(1).strip() if m else s.strip()

def _to_agent_output(obj: Any) -> AgentOutput:
    """Best-effort coercion to AgentOutput."""
    # Already an AgentOutput
    if isinstance(obj, AgentOutput):
        return obj

    # Bytes → str
    if isinstance(obj, (bytes, bytearray)):
        obj = obj.decode("utf-8", "replace")

    # String → try JSON → else wrap as completed/result
    if isinstance(obj, str):
        s = _strip_fences(obj)
        try:
            obj = json.loads(s)
        except Exception:
            return AgentOutput(status="completed", result=s, error=None)

    # Pydantic/BaseModel-ish
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()

    # Dict → try strict validate; if not present, infer
    if isinstance(obj, dict):
        # Perfect match
        if {"status", "result", "error"} <= obj.keys():
            try:
                return AgentOutput.model_validate(obj)
            except ValidationError:
                pass
        # Infer minimal AgentOutput
        status = obj.get("status")
        if status not in ("completed", "failed"):
            status = "failed" if "error" in obj else "completed"
        result = obj.get("result")
        error = obj.get("error")
        if status == "completed" and result is None:
            # Use the dict itself as a summary if no result given
            result = json.dumps(obj, ensure_ascii=False)
        if status == "failed" and error is None:
            error = json.dumps(obj, ensure_ascii=False)
        return AgentOutput(status=status, result=result if status=="completed" else None, error=error if status=="failed" else None)

    # List/other → stringify as a completed result
    try:
        return AgentOutput(status="completed", result=json.dumps(obj, ensure_ascii=False), error=None)
    except Exception:
        return AgentOutput(status="completed", result=str(obj), error=None)

# -------------------------
# Minimal no-op tool ("call another thing" = pass)
# -------------------------
class NoOpTool(Tool):
    name = "noop_other_thing"
    description = "A no-op placeholder. Call it when availability is confirmed."
    inputs = {
        "reason": {"type": "string", "description": "Why this was called", "optional": True, "nullable": True}
    }
    output_type = "object"

    def forward(self, reason: Optional[str] = None) -> Dict[str, Any]:
        return {"ok": True, "reason": reason or "availability confirmed"}

# -------------------------
# Auth helper (Calendar)
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_creds() -> Credentials:
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Make sure you have a Google Cloud OAuth client in credentials.json
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent",
                include_granted_scopes="true",
            )
        with open("token.json", "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds

# -------------------------
# Singleton BookingAgent class
# -------------------------
class BookingAgent:
    _instance = None
    _agent = None
    _token = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BookingAgent, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._agent = None
            self._token = None
    
    def _get_agent(self) -> CodeAgent:
        """Lazy initialization of the agent - only created when first needed"""
        if self._agent is None:
            if self._token is None:
                creds = get_creds()
                self._token = creds.token

            model_kwargs = {}
            model_kwargs["response_mime_type"] = "application/json"
            
            model = LiteLLMModel(
                model_id="gemini/gemini-2.5-flash",
                api_key=os.getenv("GOOGLE_API_KEY"),
                model_kwargs=model_kwargs,
            )
            tools = [
                GoogleCalendarAvailabilityTool(self._token),
                NoOpTool(),
                GoogleCalendarCreateEventTool(self._token),
            ]
            self._agent = CodeAgent(tools=tools, model=model, additional_authorized_imports=['json'])
        return self._agent
    
    def create_appointment(
        self,
        start_iso: str = "2025-09-27T11:00:00+02:00",
        end_iso: str   = "2025-09-27T12:00:00+02:00",
        summary: str   = "Appointment",
        timezone: str  = "Europe/Berlin",
        location: str = "TBD",
        description: str = "Auto-created by agent",
        calendar_id: str = "primary",
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an appointment in the user's calendar.
        
        Args:
            start_iso: Start time in ISO format (e.g., "2025-10-27T12:00:00+02:00")
            end_iso: End time in ISO format (e.g., "2025-10-27T13:00:00+02:00")
            summary: Event title
            timezone: IANA timezone for the event (e.g., "Europe/Berlin")
            location: Event location (default: "TBD")
            description: Event description (default: "Auto-created by agent")
            calendar_id: Calendar ID (default: "primary")
            attendees: List of attendee emails (optional)
        
        Returns:
            Dict with creation result
        """
        task = f"""
        You are a strict calendar assistant. ONLY use the following tools:
        1) GoogleCalendarAvailabilityTool to check the user's calendar availability for the exact time range provided.
        2) noop_other_thing once availability is confirmed.
        3) GoogleCalendarCreateEventTool to add the event to the user's calendar.

        DO NOT call any tool unrelated to the user's calendar.
        DO NOT transform or post-process tool outputs; just use their results to decide next steps.
        If the slot is busy, STOP and return a message that the time is not available.
        If the slot is free, call noop_other_thing (with a short reason), then create the event.

        Parameters for GoogleCalendarCreateEventTool:
        - summary: "{summary}"
        - start_iso: "{start_iso}"
        - end_iso: "{end_iso}"
        - timezone: "{timezone}"
        - calendar_id: "{calendar_id}"
        - description: "{description}"
        - location: "{location}"
        - attendees: {attendees or []}

        Step plan:
        - Call GoogleCalendarAvailabilityTool with the start/end ISO datetimes.
        - If available == true: call noop_other_thing.
        - Then call GoogleCalendarCreateEventTool with the same token and the event fields.
        - Return a short JSON with {{ "created": true/false, "start": start_iso, "end": end_iso }}.
        """
        
        agent = self._get_agent()
        try:
            raw = agent.run(task=task)
        except Exception as e:
            return AgentOutput(status="failed", result=None, error=f"Agent error: {e}")
        return _to_agent_output(raw)
    
    def check_availability(self, days_ahead: int = 7, calendar_ids: Optional[List[str]] = None,
                          timezone: str = "UTC", work_start_hour: int = 9, work_end_hour: int = 18) -> Dict[str, Any]:
        """
        Check calendar availability for the next N days.
        
        Args:
            days_ahead: Number of days ahead to check (default: 7)
            calendar_ids: Calendar IDs to check (default: ["primary"])
            timezone: IANA timezone for working hours (default: "UTC")
            work_start_hour: Daily working window start hour (default: 9)
            work_end_hour: Daily working window end hour (default: 18)
        
        Returns:
            Dict with availability information
        """
        task = f"""
        Check calendar availability using GoogleCalendarAvailabilityTool with these parameters:
        - days_ahead: {days_ahead}
        - calendar_ids: {calendar_ids or ["primary"]}
        - timezone: "{timezone}"
        - work_start_hour: {work_start_hour}
        - work_end_hour: {work_end_hour}
        
        Return the availability result.
        """
        
        agent = self._get_agent()
        try:
            raw = agent.run(task=task)
        except Exception as e:
            return AgentOutput(status="failed", result=None, error=f"Agent error: {e}")
        return _to_agent_output(raw)


# -------------------------
# Lazy singleton instance for easy importing
# -------------------------
# def get_booking_agent() -> BookingAgent:
#     """Lazy initialization of the global booking agent instance"""
#     if not hasattr(get_booking_agent, '_instance'):
#         get_booking_agent._instance = BookingAgent()
#     return get_booking_agent._instance

# # -------------------------
# # Convenience functions for backward compatibility
# # -------------------------
# def create_appointment(start_iso: str, end_iso: str, summary: str, timezone: str,
#                       location: str = "TBD", description: str = "Auto-created by agent", 
#                       calendar_id: str = "primary", attendees: Optional[List[str]] = None) -> Dict[str, Any]:
#     """Convenience function to create an appointment"""
#     return get_booking_agent().create_appointment(start_iso, end_iso, summary, timezone, location, description, calendar_id, attendees)

# def check_availability(days_ahead: int = 7, calendar_ids: Optional[List[str]] = None,
#                       timezone: str = "UTC", work_start_hour: int = 9, work_end_hour: int = 18) -> Dict[str, Any]:
#     """Convenience function to check availability"""
#     return get_booking_agent().check_availability(days_ahead, calendar_ids, timezone, work_start_hour, work_end_hour)

# -------------------------
# Debug Main Function
# -------------------------
# def main() -> None:
#     """Debug main function for testing the booking agent"""
#     print("=== Testing BookingAgent (Lazy) ===")
    
#     # Test lazy initialization
#     print("\n--- Testing lazy initialization ---")
#     print("Creating booking agent instance...")
#     agent = get_booking_agent()
#     print(f"Agent created: {type(agent)}")
    
#     # Test availability check
#     print("\n--- Testing availability check ---")
#     try:
#         availability = agent.check_availability(
#             days_ahead=7,
#             timezone="Europe/Berlin",
#             work_start_hour=9,
#             work_end_hour=18
#         )
#         print(f"Availability check successful: {type(availability)}")
#         if isinstance(availability, dict) and "error" in availability:
#             print(f"Error: {availability['error']}")
#         else:
#             print("Availability data retrieved successfully!")
#     except Exception as e:
#         print(f"Availability check failed: {e}")
    
#     # Test appointment creation
#     print("\n--- Testing appointment creation ---")
#     try:
#         start_iso = "2025-10-27T12:00:00+02:00"
#         end_iso = "2025-10-27T13:00:00+02:00"
#         summary = "Test appointment"
#         timezone = "Europe/Berlin"
#         location = "Test location"
#         description = "Debug test appointment"
        
#         result = agent.create_appointment(
#             start_iso, end_iso, summary, timezone, location, description
#         )
#         print(f"Appointment creation result: {type(result)}")
#         if isinstance(result, dict) and "error" in result:
#             print(f"Error: {result['error']}")
#         else:
#             print("Appointment creation successful!")
#     except Exception as e:
#         print(f"Appointment creation failed: {e}")
    
#     # Test convenience functions
#     print("\n--- Testing convenience functions ---")
#     try:
#         # Test create_appointment function
#         result1 = create_appointment(
#             "2025-10-28T14:00:00+02:00",
#             "2025-10-28T15:00:00+02:00", 
#             "Convenience test",
#             "Europe/Berlin"
#         )
#         print(f"Convenience create_appointment: {type(result1)}")
        
#         # Test check_availability function
#         result2 = check_availability(days_ahead=3, timezone="UTC")
#         print(f"Convenience check_availability: {type(result2)}")
        
#     except Exception as e:
#         print(f"Convenience functions failed: {e}")

# if __name__ == "__main__":
#     main()
