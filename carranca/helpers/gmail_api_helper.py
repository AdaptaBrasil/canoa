# gmail_helper.py
"""
Central email helper using the Google Gmail API.
Selects between OAuth 2.0 (User Account) and Service Account (DWD)
based on application configuration.
"""
import base64
from os import path
from typing import Type
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from .email_helper import RecipientsDic
from .py_helper import is_str_none_or_empty

from .gmail_dwd_helper import get_gmail_service_dwd
from .gmail_oauth_helper import get_gmail_service_oauth
from googleapiclient.discovery import build


# --- Internal: Common Message Construction Logic ---

def _create_mime_message(
    recipients: RecipientsDic,
    subject: str,
    content: str,
    sender_email: str,
    file_to_send_full_name: str = '',
    file_to_send_type: str = '',
) -> bytes:
    """
    Constructs the MIME message object including recipients, subject, body, and attachments.
    Returns the raw message bytes, ready for base64 encoding.
    """
    message = MIMEMultipart()

    # 1. Set Recipients
    message["to"] = ", ".join(
        [recipients.to.parse(item)[0] for item in recipients.to.list()]
    )
    if recipients.cc.list():
        message["cc"] = ", ".join(
            [recipients.cc.parse(item)[0] for item in recipients.cc.list()]
        )
    if recipients.bcc.list():
        # BCC addresses are handled by the API itself when using the 'raw' message format
        message["bcc"] = ", ".join(
            [recipients.bcc.parse(item)[0] for item in recipients.bcc.list()]
        )

    message["from"] = sender_email
    message["subject"] = subject

    # 2. Attach HTML body
    message.attach(MIMEText(content, "html"))

    # 3. Handle Attachment
    if not is_str_none_or_empty(file_to_send_full_name) and path.exists(
        file_to_send_full_name
    ):
        main_type, sub_type = (
            file_to_send_type.split("/") if file_to_send_type else ("application", "octet-stream")
        )
        with open(file_to_send_full_name, "rb") as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())

        encoders.encode_base64(part)
        file_name = path.basename(file_to_send_full_name)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {file_name}",
        )
        message.attach(part)

    return message.as_bytes()


# --- Public Sender Function ---

def send_mail(
    recipients: RecipientsDic,
    subject: str,
    content: str,
    file_to_send_full_name: str= '',
    file_to_send_type: str= '',
) -> str:
    """
    Sends an email using the Gmail API, selecting the authentication method based on config.

    Args:
        recipients: A RecipientsDic object with to, cc, and bcc lists.
        subject: The email subject.
        content: The body of the email.
        file_to_send_full_name: Full path to an attachment file.
        file_to_send_type: MIME type of the attachment.

    Returns:
        The successful message ID (str).

    Raises:
        ValueError: If the EMAIL_ORIGINATOR is missing or invalid.
        Exception: If any error occurs during authentication or sending (e.g., HttpError).
    """
    # Import necessary configuration variables
    from ..common.app_context_vars import sidekick

    sender_email = sidekick.config.EMAIL_ORIGINATOR
    if is_str_none_or_empty(sender_email):
        raise ValueError("Unknown 'email originator'. Cannot send email.")

    # --- Authentication Selection Logic ---

    scopes = ["https://www.googleapis.com/auth/gmail.send"]
    service: Type[build]

    # Check configuration flag to select DWD or OAuth
    if getattr(sidekick.config, "USE_SERVICE_ACCOUNT_DWD", False):
        # Use Service Account Client (DWD)
        service = get_gmail_service_dwd(
            storage_path=sidekick.config.LOCAL_STORAGE_PATH,
            sender_email=sender_email,
            scopes=scopes
        )
    else:
        # Default to OAuth 2.0 (User Account)
        service = get_gmail_service_oauth(sidekick.config.LOCAL_STORAGE_PATH)

    # --- Message Creation ---
    raw_message_bytes = _create_mime_message(
        recipients,
        subject,
        content,
        sender_email,
        file_to_send_full_name,
        file_to_send_type
    )

    # --- Encoding and Sending ---
    raw_message_b64 = base64.urlsafe_b64encode(raw_message_bytes).decode()
    create_message = {"raw": raw_message_b64}

    try:
        # Execute the send operation. Exceptions (HttpError, etc.) will be raised here.
        sent_message = service.users().messages().send(
            userId="me", body=create_message
        ).execute()
    except Exception as e:
        # Re-raise the exception to allow the calling function to handle logging/failure.
        raise e

    message_id = sent_message.get("id")

    if not message_id:
        # Safety check for an unexpected successful response without an ID.
        raise Exception(f"API response missing message ID: {sent_message}")

    return message_id

# eof