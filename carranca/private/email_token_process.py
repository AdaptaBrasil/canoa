"""
Tests and confirms that the email and sending functionality
is configured and working correctly.

mgd 2025.10.29 -- 2026.03.20
"""

# cSpell: ignore formdata FlaskForm timestamping

import random

# flask_wtf is squiggly
from typing import cast
from datetime import datetime, timedelta
from flask_wtf import FlaskForm

from .wtforms import EmailTokenForm
from ..models.public import get_user_where, persist_user
from ..helpers.py_helper import is_str_none_or_empty, datetime_for_ui
from ..public.ups_handler import get_ups_jHtml
from ..helpers.types_helper import Usual_dict
from ..helpers.route_helper import get_form_input_value
from ..helpers.jinja_helper import Jinja_generated_html, process_template
from ..helpers.email_helper import RecipientsDic, RecipientsList, send_email
from ..helpers.route_helper import get_private_response_data, init_response_vars, is_method_get
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import ModuleErrorCode
from ..helpers.ui_db_texts_manager import (
    set_msg_success,
    set_msg_error,
    set_msg_info,
    MSG_DEFAULT,
)


def _send_email(
    ui_section: str,
    email: str,
    name: str,
    vars: Usual_dict,
    msg_only: bool,
    fform: FlaskForm,
) -> Jinja_generated_html:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_CHECK)
    try:
        tmpl_ffn, _, ui_db_texts = get_private_response_data(ui_section)
        task_code += 1
        recipients = RecipientsDic(RecipientsList(email, name))
        task_code += 1
        vars.update({"user": name})

        email_sent = send_email(recipients, ui_section, vars)
        task_code += 1
        if email_sent:
            set_msg_success("emailSentSuccess", ui_db_texts)
            ui_db_texts.display_msg_only = msg_only
        else:
            set_msg_error("emailSentError", ui_db_texts)

        task_code += 1
        jHtml = process_template(tmpl_ffn, form=fform, **vars, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("emailSentException", ui_db_texts, task_code, e)

    return jHtml


def has_token_expired(sent_at: datetime | None) -> bool:
    """
    Checks if the verification window has closed.
    Relies on the DB-generated timestamp for maximum precision.
    """
    if sent_at is None:
        # No timestamp means the token was either cleared by the trigger
        # or never generated. In both cases, it's 'expired/invalid'.
        return True

    # Hours defined in sidekick.config (e.g., 8)
    limit_hours = int(sidekick.config.email_verify_token_expires_hours)

    # Calculate the deadline
    expiration_deadline = sent_at + timedelta(hours=limit_hours)

    # Compare with current application time
    return sidekick.now() > expiration_deadline


def send_email_to_test_address(email: str, name: str) -> Jinja_generated_html:
    """
    Sends a test email to the user's registered address to verify
    email deliverability and sending engine functionality.
    """

    fform = FlaskForm(formdata=None)
    jHtml = _send_email("emailToTestEmail", email, name, {}, True, fform)

    return jHtml


def send_token_and_verify(email: str, name: str) -> Jinja_generated_html:
    """
    emails the token and returns a form for the user to inform it
    """

    def __generate_token(digit_count: int) -> int:
        """Internal helper for string-based tokens."""
        low = 10 ** (digit_count - 1)
        high = (10**digit_count) - 1
        return random.randint(low, high)

    vars = {}
    if is_method_get():
        digit_count = sidekick.config.email_verify_token_digit_count
        token = __generate_token(digit_count)

        # Persistence triggers the DB's automated timestamping
        user_rec = get_user_where(email=email)
        user_rec.verify_email_token = str(token)
        persist_user(user_rec)

        # Prepare email variables including the new 'hours' logic
        vars.update({"token": token, "expires": sidekick.config.email_verify_token_expires_hours})

    fform = EmailTokenForm()

    jHtml = _send_email("verifySentToken", email, name, vars, False, fform)

    return jHtml


def verify_sent_token(email: str, db_token: str, email_sent_at: datetime) -> Jinja_generated_html:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_VERIFY)
    code = 0
    try:

        def _get_time_info(sent_at: datetime) -> str:
            """Updates the UI labels like 'today at 14:00' using DB time."""
            days = (sidekick.now().date() - sent_at.date()).days
            time_str = sent_at.strftime("%H:%M")

            if days == 0:
                label = ui_db_texts.format("sendToday", time_str)
            elif days == 1:
                label = ui_db_texts.format("sendYesterday", time_str)
            else:
                label = ui_db_texts.format("sendDate", datetime_for_ui(sent_at))

            return label

        fform = EmailTokenForm()
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("verifySentToken")

        # keep info, GET and POST (because it can have a warn|error)
        time_info = _get_time_info(email_sent_at)
        set_msg_info(MSG_DEFAULT, ui_db_texts, time_info)

        if is_get:
            jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())
            return jHtml

        # is post
        def _set_msg_error(code: int, error_hint: str):
            set_msg_error(MSG_DEFAULT, ui_db_texts, task_code + code, error_hint)
            return

        code = 1
        if is_str_none_or_empty(ui_token := cast(str, get_form_input_value(fform.token.name))):
            _set_msg_error(code + 2, "msg_TokenNotFound")
        elif not (db_token == ui_token):
            set_msg_error("wrongToken", ui_db_texts)
        elif not (user_rec := get_user_where(email=email)):
            _set_msg_error(code + 4, "msg_UserNotFound")
        elif has_token_expired(email_sent_at):
            _set_msg_error(code + 5, "msg_TokenExpired")
        else:
            code += 6
            user_rec.verify_email_token = ui_token + "*"  # the key to unlock the e-mail.
            persist_user(user_rec)
            set_msg_success(MSG_DEFAULT, ui_db_texts)

        jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())

    except Exception as e:
        task_code = task_code + code
        jHtml = get_ups_jHtml(MSG_DEFAULT, ui_db_texts, task_code, e)

    return jHtml


# eof
