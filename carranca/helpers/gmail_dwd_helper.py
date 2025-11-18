# gmail_dwd_helper.py
"""
Service Account authentication handler with Domain-Wide Delegation (DWD) for the Gmail API.
This module uses a key file to impersonate a user within a Google Workspace domain.
"""
from os import path
from typing import Type

from googleapiclient.discovery import build

try:
    from google.oauth2.service_account import Credentials
except ImportError as e:
    raise ImportError(
        "The 'google-api-python-client' and 'google-auth' libraries are required for "
        "Service Account authentication. Please install them."
    ) from e

# --- Configuration Constants ---
SERVICE_ACCOUNT_FILENAME = "canoa-gmail-key.json"


def get_gmail_service_dwd(
    storage_path: str, sender_email: str, scopes: list[str]
) -> Type[build]:
    """
    Authenticates using Service Account with DWD and returns the Gmail API service object.

    Args:
        storage_path: Directory where the Service Account key file resides.
        sender_email: The email address of the user (in the Google Workspace domain)
                      to impersonate (the 'subject' for DWD).
        scopes: List of Google API scopes to use.

    Returns:
        The authenticated Gmail API service object.

    Raises:
        ValueError: If the sender_email is invalid or missing.
        FileNotFoundError: If the Service Account key file is not found.
    """
    # Local import to avoid dependence on 'sidekick' outside the helper layer
    from .py_helper import is_str_none_or_empty

    if is_str_none_or_empty(sender_email):
        raise ValueError("Unknown 'email originator'. Cannot perform DWD authentication.")

    service_account_file = path.join(storage_path, SERVICE_ACCOUNT_FILENAME)

    if not path.isfile(service_account_file):
        raise FileNotFoundError(
            f"Gmail service account key not found at {service_account_file}"
        )

    # Core DWD logic: The 'subject' parameter specifies the user to impersonate.
    creds = Credentials.from_service_account_file(
        service_account_file, scopes=scopes, subject=sender_email
    )

    # Build the Gmail API service
    service = build("gmail", "v1", credentials=creds)

    return service

#eof