import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SERVICE_ACCOUNT_FILE = 'secret.json'
USER_EMAIL = 'wonhyukc@stu.ac.kr'

def test_gmail_api():
    try:
        # Load service account credentials and set the user to impersonate
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        # Enable domain-wide delegation
        creds = creds.with_subject(USER_EMAIL)
        
        # Build the Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Try a simple API call: getting the user's profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"Successfully connected to Gmail API as {USER_EMAIL}")
        print(f"Total messages: {profile.get('messagesTotal')}")
    except Exception as e:
        print(f"Failed to access Gmail API: {e}")

if __name__ == '__main__':
    test_gmail_api()
