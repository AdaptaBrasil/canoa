"""
Tests and confirms that the email and sending functionality
is configured and working correctly.

mgd 2025.10.29 -- 2026.03.20
"""

# cSpell: ignore formdata FlaskForm timestamping

import random

# flask_wtf is squiggly
from typing import Tuple, cast
from datetime import datetime, timedelta
from flask_wtf import FlaskForm

from ..wtforms import EmailTokenForm
from ...models.public import get_user_where, persist_user
from ...public.ups_handler import get_ups_jHtml
from ...helpers.py_helper import is_str_none_or_empty, generate_random, crc16
from ...helpers.types_helper import Usual_Dict
from ...helpers.jinja_helper import Jinja_Rendered, process_template
from ...helpers.email_helper import RecipientsDic, RecipientsList, send_email
from ...helpers.route_helper import (
    get_account_response_data,
    get_form_input_value,
    init_response_vars,
    private_route,
    is_method_post,
    is_method_get,
)
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.ui_db_texts_manager import UITextsKeys, MSG_DEFAULT


def _uid(user_email):
    return f"{crc16('ui_' + user_email):04x}"


def _send_email(
    ui_section: str,
    email: str,
    name: str,
    vars: Usual_Dict,
    msg_only: bool,
    fform: FlaskForm,
) -> Tuple[Jinja_Rendered, bool]:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_CHECK)
    sent = False
    try:
        tmpl_ffn, _, ui_db_texts = get_account_response_data(ui_section)
        task_code += 1
        recipients = RecipientsDic(RecipientsList(email, name))
        task_code += 1
        vars.update({"user": name})

        email_sent = send_email(recipients, ui_section, vars)
        task_code += 1
        if email_sent:
            ui_db_texts.set_msg_success("emailSentSuccess")
            ui_db_texts.display_msg_only = msg_only
            sent = True
        else:
            ui_db_texts.set_msg_error("emailSentError")

        task_code += 1
        jHtml = process_template(tmpl_ffn, form=fform, **vars, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("emailSentException", ui_db_texts, task_code, e)

    return jHtml, sent


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
    limit_hours = int(sidekick.config.EMAIL_VERIFY_TOKEN_EXPIRES_HOURS)

    # Calculate the deadline
    expiration_deadline = sent_at + timedelta(hours=limit_hours)

    # Compare with current application time
    return sidekick.now() > expiration_deadline


def send_email_to_test_address(route: str, email: str, name: str) -> Jinja_Rendered:
    """
    Sends a test email to the user's registered address to verify
    email deliverability and sending engine functionality.
    """

    def _mask_email(email: str) -> str:
        user, domain = email.split("@")
        lg = len(user) - 1
        return "*" if lg < 1 else f"{user[0]}{"*" * lg}@{domain}"

    if is_method_get():
        fform = FlaskForm(formdata=None)
        jHtml, _ = _send_email("emailToTestEmail", email, name, {}, True, fform)

    else:
        jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_CHECK)
        try:
            tmpl_ffn, _, ui_db_texts = get_account_response_data("emailToTestEmail", "generic_prompt")
            task_code += 1
            masked_email = _mask_email(email)
            task_code += 1
            ui_db_texts.set_msg_info("requestEmailText", masked_email)
            ui_db_texts[UITextsKeys.Form.btn_submit] = ui_db_texts["acceptEmailBtn"]
            ui_db_texts[UITextsKeys.Form.submit_route] = private_route(route, uid="")
            ui_db_texts.display_msg_only = True
            task_code += 1
            jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

        except Exception as e:
            jHtml = get_ups_jHtml(MSG_DEFAULT, ui_db_texts, task_code, e)

        return jHtml

    return jHtml


def send_and_wait_verify_token(email: str, name: str, uid: str) -> Jinja_Rendered:
    """
    emails the token and returns a form for the user to inform it
    """

    def _update_token(token: int | None):
        # Persistence triggers the DB's automated timestamping
        user_rec = get_user_where(email=email)
        user_rec.verify_email_token = str(token)
        persist_user(user_rec)
        return

    vars = {}
    token_saved = False
    if is_method_post():
        digit_count = sidekick.config.EMAIL_VERIFY_TOKEN_DIGIT_COUNT
        token = generate_random(digit_count)
        _update_token(token)
        token_saved = True

        # Prepare email variables including the new 'hours' logic
        vars.update({"token": token, "expires": sidekick.config.EMAIL_VERIFY_TOKEN_EXPIRES_HOURS})

    fform = EmailTokenForm()

    jHtml, email_sent = _send_email("verifySentToken", email, name, vars, False, fform)
    if token_saved and not email_sent:
        _update_token(None)

    return jHtml


def explain_email_addr_proc(route: str, user_email: str) -> Jinja_Rendered:
    """Explains the user email address verification process and ask permission to start it (sending an email)"""

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_VERIFY)
    task_code += 10
    try:
        tmpl_ffn, _, ui_db_texts = get_account_response_data("verifySentToken", "generic_prompt")
        ui_db_texts.set_msg_info("acceptEmail")
        ui_db_texts[UITextsKeys.Form.btn_submit] = ui_db_texts["acceptEmailBtn"]
        ui_db_texts[UITextsKeys.Form.submit_route] = private_route(route, uid=_uid(user_email))
        ui_db_texts.display_msg_only = True
        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml(MSG_DEFAULT, ui_db_texts, task_code, e)

    return jHtml


def verify_sent_token(email: str, db_token: str, email_sent_at: datetime) -> Jinja_Rendered:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_VERIFY)
    code = 0
    try:
        fform = EmailTokenForm()
        tmpl_ffn, is_get, ui_db_texts = get_account_response_data("verifySentToken")

        # keep info, GET and POST (because it can have a warn|error)
        days = (email_sent_at.date() - sidekick.now().date()).days
        time_info = ui_db_texts.get_ui_datetime(days, email_sent_at, "days")
        expiry = sidekick.config.EMAIL_VERIFY_TOKEN_EXPIRES_HOURS
        ui_db_texts.set_msg_info(MSG_DEFAULT, (time_info, expiry))

        if is_get:
            jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())
            return jHtml

        # is post
        def _set_msg_error(code: int, error_hint: str):
            ui_db_texts.set_msg_error(MSG_DEFAULT, (task_code + code, error_hint))
            return

        code = 1
        if is_str_none_or_empty(ui_token := cast(str, get_form_input_value(fform.token.name))):
            _set_msg_error(code + 2, "msg_TokenNotFound")
        elif not (db_token == ui_token):
            ui_db_texts.set_msg_error("wrongToken")
        elif not (user_rec := get_user_where(email=email)):
            _set_msg_error(code + 4, "msg_UserNotFound")
        elif has_token_expired(email_sent_at):
            _set_msg_error(code + 5, "msg_TokenExpired")
        else:
            code += 6
            user_rec.verify_email_token = ui_token + "*"  # the key to unlock the e-mail.
            persist_user(user_rec)
            ui_db_texts.set_msg_success()

        jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())

    except Exception as e:
        task_code = task_code + code
        jHtml = get_ups_jHtml(MSG_DEFAULT, ui_db_texts, task_code, e)

    return jHtml


# eof
