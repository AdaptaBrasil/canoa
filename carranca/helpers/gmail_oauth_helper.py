# oauth_client.py
"""
OAuth 2.0 authentication handler for the Gmail API.
This module manages user credentials (token.json), refreshing them if expired,
or initiating a new authorization flow if tokens are missing.
"""
from os import path
from typing import Type

from googleapiclient.discovery import build

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError as e:
    raise ImportError(
        "The 'google-auth-oauthlib' and 'google-api-python-client' libraries "
        "are required for OAuth 2.0. Please install them."
    ) from e


# --- Configuration Constants ---
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CLIENT_SECRETS_FILENAME = "canoa-gmail-oauth.json" # The client_secrets file downloaded from GCP
TOKEN_FILENAME = "token.json"


def _get_credentials(json_path: str) -> Credentials:
    """
    Manages the lifecycle of user credentials (token, refresh, flow).

    Args:
        json_path: The directory path where token.json and the client secrets file reside.

    Returns:
        A valid Google Credentials object.

    Raises:
        FileNotFoundError: If the initial client secrets file is missing.
    """
    creds = None
    token_ffn = path.join(json_path, TOKEN_FILENAME)
    credentials_ffn = path.join(json_path, CLIENT_SECRETS_FILENAME)

    # 1. Check for existing token
    if path.exists(token_ffn):
        creds = Credentials.from_authorized_user_file(token_ffn, SCOPES)

    # 2. Check validity and refresh if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh token if expired but refreshable
            creds.refresh(Request())
        else:
            # Start new authorization flow if token is missing or invalid
            if not path.exists(credentials_ffn):
                raise FileNotFoundError(
                    f"OAuth credentials file not found at {credentials_ffn}. "
                    "Please create it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_ffn, SCOPES)
            creds = flow.run_local_server(port=0)

        # 3. Save the updated or new credentials for the next run
        with open(token_ffn, "w") as token:
            token.write(creds.to_json())

    return creds

def get_gmail_service_oauth(config_path: str) -> Type[build]:
    """
    Authenticates using OAuth 2.0 and returns the Gmail API service object.

    Args:
        config_path: The directory path containing the authentication files.

    Returns:
        The authenticated Gmail API service object.
    """
    creds = _get_credentials(config_path)
    # The 'build' function is imported globally for clarity in this file
    return build("gmail", "v1", credentials=creds)

# eof