"""
Central email helper using Flask-Mail with SMTP.
Requires a Flask application context and the 'mail' extension initialized.
"""

# cSpell:ignore SMTP

from os import path
from typing import Optional

from flask_mail import Message

from .py_helper import is_str_none_or_empty, get_params
from .types_helper import UsualDict
from .email_helper import RecipientsDic, RecipientsList
from .ui_db_texts_helper import get_section
from ..common.app_constants import APP_NAME
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import ModuleErrorCode


# --- Internal Sender Function ---
# ---    see email_helper.py   ---


def _send_email(
    recipients: RecipientsDic,
    texts_or_section: UsualDict | str,
    text_values: Optional[UsualDict] = None,
    file_to_send_full_name: str = "",
    file_to_send_type: str = "",
) -> bool:
    """
     ⚠️ _send_email:
        This function is the internal implementation for the [Flask SMTP] email API and should
        only be called by the central public send_email wrapper.

    Sends an email using the Flask-Mail SMTP service.

    Args:
        recipients: The recipient information.
            If a RecipientsList is used, it's assumed to be the "to" recipient.

        texts_or_section: (dict or str)
            if str, is an entry of .ui_texts_helper.get_section that returns a dict
            if Dict[str, str], it is used directly.
            Expected dict Keys:
                # NOTE:
                subject=texts["subject"],
                html_content=texts["content"],

        text_values: Optional[ Dict[key: str, value: str] ]
            values to substitute {key} in the content, subject
            As usual, use double curly braces {{key}} in the .ui_texts to avoid early substitution by str.format().

        file_to_send_full_name: Optional[str]
            full path and name of file to attach to the mail

    Returns:
        Bool: True if the email was sent successfully, False otherwise.

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

    db_texts = {}
    task_code = ModuleErrorCode.SEND_EMAIL.value
    try:

        if isinstance(texts_or_section, dict):
            task_code += 1
            db_texts = texts_or_section.copy()
        elif not is_str_none_or_empty(texts_or_section):
            task_code += 2
            db_texts = get_section(texts_or_section)
        else:
            task_code += 3

        email_text = db_texts.get("text", "")  # no HTML content, just text
        email_content = db_texts.get("content", "")
        email_subject = db_texts.get("subject", APP_NAME)

        params = get_params(email_text) + get_params(email_content) + get_params(email_subject)
        # if collision, text_values take precedence over db_texts
        available = {**(db_texts or {}), **(text_values or {})}
        missing = [p for p in params if p not in available]
        if missing:
            sidekick.display.error(f"Missing placeholders in body_values &| db_texts: {missing}")

        email_text = email_text.format(**available)
        email_content = email_content.format(**available)
        email_subject = email_subject.format(**available)

        task_code += 1
        sender = RecipientsList(sidekick.config.EMAIL_ORIGINATOR, APP_NAME).parse("")
        msg = Message(
            subject=email_subject,
            sender=sender,
            recipients=[recipients.to.parse(item) for item in recipients.to.list()],
            cc=(
                [recipients.cc.parse(item) for item in recipients.cc.list()]
                if recipients.cc.list()
                else None
            ),
            bcc=(
                [recipients.bcc.parse(item) for item in recipients.bcc.list()]
                if recipients.bcc.list()
                else None
            ),
            html=email_content,
            body=email_text,
        )

        # 3. Handle Attachment (Simplified)
        task_code += 1
        if is_str_none_or_empty(file_to_send_full_name):
            pass
        elif not path.exists(file_to_send_full_name):
            raise ValueError(f"Attachment file not found [{file_to_send_full_name}].")
        else:
            task_code += 1
            with sidekick.app.open_resource(file_to_send_full_name) as fp:
                msg.attach(
                    filename=path.basename(file_to_send_full_name),
                    data=fp.read(),
                    # TODO file_to_send_type
                    # MIME type is often inferred, but for safety, you could pass file_to_send_type
                    # Example of passing type: content_type=file_to_send_type
                )

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
