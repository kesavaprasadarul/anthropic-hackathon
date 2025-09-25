
# import os
# import json
# import time
# import requests
# from typing import List, Dict, Any, Optional

# from globals import *
# from smolagents import Tool, CodeAgent
# from smolagents.models import LiteLLMModel
# from tools import GoogleCalendarCreateEventTool, GoogleCalendarAvailabilityTool, CombinedReservationSearchTool
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials

# details_headers = {
#     "Content-Type": "application/json",
#     "X-Goog-Api-Key": GOOGLE_API_KEY,
#     "X-Goog-FieldMask": (
#         "id,displayName,formattedAddress,googleMapsUri,"
#         "reservable,websiteUri,internationalPhoneNumber,nationalPhoneNumber,"
#         "currentOpeningHours,rating,userRatingCount,priceLevel"
#     )
# }


# def build_agent() -> CodeAgent:
#     model = LiteLLMModel(
#         model_id="gemini/gemini-2.5-flash-lite",
#         api_key=os.getenv("GEMINI_KEY"),
#     )
#     tools = [CombinedReservationSearchTool(), GoogleCalendarAvailabilityTool(), GoogleCalendarCreateEventTool()]
#     return CodeAgent(tools=tools, model=model)



# def main() -> None:

#     ipinfo = requests.get("https://ipinfo.io/json").json()
#     lat, lon = map(float, ipinfo["loc"].split(","))

#     SCOPES = ['https://www.googleapis.com/auth/calendar']

#     def get_creds():
#         creds = None
#         if os.path.exists('token.json'):
#             creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#                 creds = flow.run_local_server(
#                     port=0,
#                     access_type='offline',
#                     prompt='consent',                # <= ensures refresh token
#                     include_granted_scopes='true'
#                 )
#             with open('token.json', 'w') as f:
#                 f.write(creds.to_json())
#         return creds

#     creds = get_creds()
#     token = creds.token

#     task = (
#         f"""
#         You are an assistant that helps users make reservations of some appointments to places nearby,
#         like a restaurant, a hairdresser's, cinema etc.

#         The user is located approximately in {lat}, {lon}. You have tools to find the hairdressers nearby.

#         They would like to attend an appointment at 12:00 on Saturday 27.06. Check if the date and time is availabkle in the calendar.

#         In the radius of 2 km of the user, find 5 options of hairdresser

#         Use only the tools available and dont add any code processing of the output.

#         In the end, return the name of the place, the booking phone and/or website, as well as the list of available times for booking.

#         Also, add the slot in the user's calendar

#         The calendar token is {token}
#         """
#     )
    

#     agent = build_agent()

#     places: List[Dict[str, Any]] = agent.run(
#         task=task,
#     )
#     # if isinstance(places, str):
#     #     try:
#     #         places = json.loads(places)
#     #     except Exception:
#     #         raise SystemExit("Agent did not return JSON. Please try again.")


# if __name__ == "__main__":
#     main()


import os
import json
from typing import List, Dict, Any, Optional

from smolagents import Tool, CodeAgent
from smolagents.models import LiteLLMModel

from tools import GoogleCalendarCreateEventTool, GoogleCalendarAvailabilityTool
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

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
# Build agent limited to calendar-only behavior
# -------------------------
def build_agent(token) -> CodeAgent:
    model = LiteLLMModel(
        model_id="gemini/gemini-2.5-flash-lite",
        api_key=os.getenv("GEMINI_KEY"),
    )
    tools = [
        GoogleCalendarAvailabilityTool(token),   # expects token + datetime range
        NoOpTool(),                         # the "other thing"
        GoogleCalendarCreateEventTool(token),    # create the event if free
    ]
    # No other tools added on purpose
    return CodeAgent(tools=tools, model=model)

# -------------------------
# Main
# -------------------------
def main() -> None:
    creds = get_creds()
    token = creds.token

    # 👉 Supply an explicit ISO 8601 datetime and timezone to avoid ambiguity.
    # Example target slot: 2025-06-27 12:00–13:00 Europe/Berlin
    # Adjust as needed or parse user input before crafting the task.
    start_iso = "2025-10-27T12:00:00+02:00"  # Europe/Berlin on June 27, 2025 is CEST (UTC+02:00)
    end_iso   = "2025-10-27T13:00:00+02:00"
    summary   = "Haircut appointment"
    location  = "TBD"
    description = "Auto-created by agent after availability check."

    # Clear, tool-oriented instructions so the LLM does exactly 3 things:
    task = f"""
You are a strict calendar assistant. ONLY use the following tools:
1) GoogleCalendarAvailabilityTool to check the user's calendar availability for the exact time range provided.
2) noop_other_thing once availability is confirmed.
3) GoogleCalendarCreateEventTool to add the event to the user's calendar.

DO NOT call any tool unrelated to the user's calendar.
DO NOT transform or post-process tool outputs; just use their results to decide next steps.
If the slot is busy, STOP and return a message that the time is not available.
If the slot is free, call noop_other_thing (with a short reason), then create the event.

Parameters:
- start_iso: "{start_iso}"
- end_iso: "{end_iso}"
- event_summary: "{summary}"
- event_location: "{location}"
- event_description: "{description}"

Step plan:
- Call GoogleCalendarAvailabilityTool with the start/end ISO datetimes.
- If available == true: call noop_other_thing.
- Then call GoogleCalendarCreateEventTool with the same token and the event fields.
- Return a short JSON with {{ "created": true/false, "start": start_iso, "end": end_iso }}.
"""

    agent = build_agent(token)
    result = agent.run(task=task)
    print(result)

if __name__ == "__main__":
    main()

