# smtp-helper.py
"""
Central email helper using Flask-Mail with SMTP.
Requires a Flask application context and the 'mail' extension initialized.
"""
from os import path
from typing import Optional

from flask_mail import Message

from .py_helper import is_str_none_or_empty
from .email_helper import RecipientsDic
from ..common.app_context_vars import sidekick


# --- Internal Sender Function ---
# ---    see email_helper.py   ---


def _send_email(
    recipients: RecipientsDic,
    subject: str,
    content: str,  # This will be used as the HTML content
    file_to_send_full_name: str = "",
    file_to_send_type: str = "",
) -> bool:
    """
     ⚠️ _send_email:
        This function is the internal implementation for the [Flask SMPT] email API and should
        only be called by the central public send_email wrapper.

    Sends an email using the Flask-Mail SMTP service.

    Args:
        recipients: A RecipientsDic object with to, cc, and bcc lists.
        subject: The email subject.
        content: The HTML body of the email.
        file_to_send_full_name: Full path to an attachment file.
        file_to_send_type: MIME type of the attachment (Flask-Mail infers this).

    Returns:
        A success message string (e.g., "Email queued successfully").

    Raises:
        ValueError: If a required configuration (like MAIL_USERNAME) is missing.
        Exception: If any error occurs during sending (e.g., SMTPAuthenticationError).
    """
    # 1. Ensure Flask context is active and mail object is available
    if not hasattr(sidekick.app, "extensions") or "mail" not in sidekick.app.extensions:
        raise RuntimeError("Flask-Mail extension is not initialized on the application.")

    # In Flask-Mail, the sender is usually configured globally,
    # but we will perform a quick check based on your old logic.
    # -- CHECKED ON INIT
    # sender_email = sidekick.app.config.get('MAIL_USERNAME')
    # if is_str_none_or_empty(sender_email):
    #     raise ValueError("MAIL_USERNAME (sender email) is missing in configuration.")

    # 2. Create the Flask-Mail Message object
    msg = Message(
        subject=subject,
        sender=sidekick.config.EMAIL_ORIGINATOR,  # Uses the configured MAIL_USERNAME as sender
        # Flask-Mail accepts lists of emails directly for recipients
        recipients=[recipients.to.parse(item)[0] for item in recipients.to.list()],
        cc=[recipients.cc.parse(item)[0] for item in recipients.cc.list()] if recipients.cc.list() else None,
        bcc=[recipients.bcc.parse(item)[0] for item in recipients.bcc.list()] if recipients.bcc.list() else None,
        html=content,  # Uses the 'content' as the HTML body
        # Note: If you need a plain text body, you'd add: body="Plain text fallback"
    )

    # 3. Handle Attachment (Simplified)
    if is_str_none_or_empty(file_to_send_full_name):
        pass
    elif not path.exists(file_to_send_full_name):
        raise ValueError(f"Attachment file not found [{file_to_send_full_name}].")
    else:
        with sidekick.app.open_resource(file_to_send_full_name) as fp:
            msg.attach(
                filename=path.basename(file_to_send_full_name),
                data=fp.read(),
                # TODO file_to_send_type
                # MIME type is often inferred, but for safety, you could pass file_to_send_type
                # Example of passing type: content_type=file_to_send_type
            )

    try:
        # Get the initialized Mail object from the app context
        mail_ext = sidekick.app.extensions["mail"]

        mail_ext.send(msg)

    except Exception as e:
        # Log the detailed error (e.g., SMTPAuthenticationError, SMTPServerDisconnected)
        sidekick.display.error(f"Failed to send email via SMTP. Error: {str(e)}")
        raise e

    # Flask-Mail sends asynchronously in production and queues the message;
    # it does not return a unique message ID like the Gmail API.
    return True


# eof
