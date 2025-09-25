from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_creds():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Force refresh token issuance:
            creds = flow.run_local_server(
                port=0,
                access_type='offline',
                prompt='consent',                # <= ensures refresh token
                include_granted_scopes='true'
            )
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    return creds

if __name__ == "__main__":
    creds = get_creds()
    print("Access token:", creds.token)
    print("Refresh token:", creds.refresh_token)  # keep this safe