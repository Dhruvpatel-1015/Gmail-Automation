"""
gmail_client.py
----------------
Handles Gmail API authentication and basic operations like reading,
listing, and sending emails using OAuth 2.0.
"""

import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# If modifying these scopes, delete token.json before running again.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


class GmailClient:
    def __init__(self):
        """
        Initialize Gmail Client.
        """
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.creds_path = os.path.join(BASE_DIR, "credentials.json")
        self.token_path = os.path.join(BASE_DIR, "token.json")

    def authenticate(self):
        """
        Handles Gmail OAuth 2.0 flow and builds the Gmail API service.
        """
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If there are no valid credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for future use
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        self.creds = creds
        self.service = build("gmail", "v1", credentials=creds)
        print("✅ Gmail authentication successful!")

    def list_messages(self, max_results=5):
        """
        Lists latest Gmail messages.
        """
        results = (
            self.service.users()
            .messages()
            .list(userId="me", maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])
        print(f"📩 Found {len(messages)} messages.")
        return messages

    def read_message(self, msg_id):
        from googleapiclient.errors import HttpError
        import base64
        from bs4 import BeautifulSoup
    
        try:
            message = self.service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            payload = message.get("payload", {})
            headers = payload.get("headers", [])
    
            # Extract sender and subject
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    
            # Decode the message body (supports multipart emails)
            body = ""
            body_html = ""
    
            def extract_parts(parts):
                nonlocal body, body_html
                for part in parts:
                    mime_type = part.get("mimeType", "")
                    data = part.get("body", {}).get("data")
                    if data:
                        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        if mime_type == "text/plain":
                            body += decoded
                        elif mime_type == "text/html":
                            body_html += decoded
                    if "parts" in part:
                        extract_parts(part["parts"])
    
            if "parts" in payload:
                extract_parts(payload["parts"])
            else:
                data = payload.get("body", {}).get("data")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    
            # If plain text is empty, extract text from HTML
            if not body and body_html:
                soup = BeautifulSoup(body_html, "html.parser")
                body = soup.get_text(separator="\n")
    
            return {
                "sender": sender,
                "subject": subject,
                "body": body.strip(),
                "body_html": body_html.strip(),
            }
    
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None


    def create_draft(self, to, subject, body):
        """
        Creates a draft email (does NOT send it).
        """
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft = (
            self.service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw_message}})
            .execute()
        )

        print(f"💾 Draft created successfully! Draft ID: {draft['id']}")
        return draft



if __name__ == "__main__":
    # Dynamically find the directory of this script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
    TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

    gmail = GmailClient(
        credentials_path=CREDENTIALS_PATH,
        token_path=TOKEN_PATH
    )

    gmail.authenticate()
    messages = gmail.list_messages(3)
    if messages:
        gmail.read_message(messages[0]["id"])