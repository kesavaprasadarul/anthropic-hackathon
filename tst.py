# from tools import *
# import os
# from typing import Tuple, List
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials

# SCOPES = ['https://www.googleapis.com/auth/calendar']

# def get_creds():
#     creds = None
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#             creds = flow.run_local_server(
#                 port=0,
#                 access_type='offline',
#                 prompt='consent',                # <= ensures refresh token
#                 include_granted_scopes='true'
#             )
#         with open('token.json', 'w') as f:
#             f.write(creds.to_json())
#     return creds

# creds = get_creds()

# # 1) Availability next 5 days in Europe/Berlin within 10–18
# avail_tool = GoogleCalendarAvailabilityTool()
# availability = avail_tool.forward(
#     days_ahead=5,
#     timezone="Europe/Berlin",
#     work_start_hour=10,
#     work_end_hour=18,
#     access_token=creds.token
# )
# print(availability)

# # 2) Create an event (only if no conflict)
# create_tool = GoogleCalendarCreateEventTool()
# # result = create_tool.forward(
# #     summary="Dinner reservation",
# #     start_iso="2025-09-25T19:30:00+02:00",
# #     end_iso="2025-09-25T21:00:00+02:00",
# #     timezone="Europe/Berlin",
# #     description="Brauhaus Rudi, table for 2",
# #     location="Example Str. 1, Berlin",
# #     access_token=creds.token
# # )
# # print(result)
# # If conflict: result = {"created": False, "conflict": True, ...}
# # If success:  result = {"created": True, "event_id": "...", "htmlLink": "...", ...}

import json
with open("data.json", "r", encoding="utf-8") as f:
    # 2. Parse JSON into a Python object (dict or list)
    data = json.load(f)

# 3. Now you can use it like a normal Python object
print(type(data))
