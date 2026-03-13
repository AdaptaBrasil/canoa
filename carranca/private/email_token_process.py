"""
Tests and confirms that the email and sending functionality
is configured and working correctly.

mgd 2025.10.29 -- 11.08
"""

# cSpell: ignore  formdata FlaskForm
import random
from flask import request
from flask_wtf import FlaskForm
from datetime import datetime, timedelta
from ..models.public import get_user_where, persist_user
from ..helpers.py_helper import is_str_none_or_empty
from ..public.ups_handler import get_ups_jHtml
from ..helpers.types_helper import Usual_dict
from ..helpers.jinja_helper import Jinja_generated_html, process_template
from ..helpers.email_helper import RecipientsDic, RecipientsList, send_email
from ..helpers.route_helper import get_private_response_data, init_response_vars, is_method_get
from ..common.app_context_vars import sidekick
from ..helpers.ui_db_texts_class import add_msg_success, add_msg_error
from ..common.app_error_assistant import ModuleErrorCode


def _get_token_expiration_date(from_dt: datetime | None) -> datetime:
    if from_dt is None:
        # ok, already expired
        return sidekick.now() - timedelta(hours=24)

    token_life_in_hours = int(sidekick.config.email_verify_token_expires_hours)
    if token_life_in_hours < 2:
        raise ValueError(f"The verification token expiration time is too short: {token_life_in_hours}h.")
    expires_at = from_dt + timedelta(hours=token_life_in_hours)
    return expires_at


def token_has_expired(from_dt: datetime | None):
    return True if from_dt is None else sidekick.now() > _get_token_expiration_date(from_dt)


def _send_email(
    ui_section: str, email: str, name: str, vars: Usual_dict, msg_only: bool, fform: FlaskForm
) -> Jinja_generated_html:

    email_sent = False
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
            add_msg_success("emailSentSuccess", ui_db_texts)
            # if requested, display form (if any)
            ui_db_texts.display_msg_only = msg_only
        else:
            add_msg_error("emailSentError", ui_db_texts)

        task_code += 1
        jHtml = process_template(tmpl_ffn, form=fform, **vars, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("emailSentException", ui_db_texts, task_code, e)

    return jHtml


def email_test_email(email: str, name: str) -> Jinja_generated_html:

    fform = FlaskForm(formdata=None)
    jHtml = _send_email("emailToTestEmail", email, name, {}, True, fform)

    return jHtml


def send_token_and_verify(email: str, name: str) -> Jinja_generated_html:
    from .wtforms import EmailTokenForm

    # AQUI FIX, se exites token, abrir input

    def __generate_token(digit_count: int) -> int:
        """Generates a random integer with exactly `digit_count` digits."""
        low = 10 ** (digit_count - 1)
        high = (10**digit_count) - 1
        return random.randint(low, high)

    vars = {}
    if is_method_get():
        token = __generate_token(sidekick.config.email_verify_token_digit_count)
        user_rec = get_user_where(email=email)
        expiration = _get_token_expiration_date(user_rec.verify_email_sent_at)
        vars.update({"expires": expiration, "user": name, "token": token})
        user_rec.verify_email_token = str(token)
        persist_user(user_rec)

    fform = EmailTokenForm()
    jHtml = _send_email("sendTokenAndVerify", email, name, vars, False, fform)

    return jHtml


def verify_sent_token(email: str, token_entered: str) -> Jinja_generated_html:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_VERIFY)
    code = 0
    try:
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("verifySentToken")

        why_msg = "msg_Unknown"
        code = 1
        if is_get:
            code += 1
        elif is_str_none_or_empty(token_entered):
            code += 2
            why_msg = "msg_NoToken"
        elif not (user_rec := get_user_where(email=email)):
            code += 3
            why_msg = "msg_UserNotFound"
        elif is_str_none_or_empty(token_read := user_rec.verify_email_token):
            code += 4
            why_msg = "msg_TokenNotFound"
        elif token_entered != token_read:
            code += 5
            why_msg = "msg_WrongToken"
        elif token_has_expired(user_rec.verify_email_sent_at):
            code += 6
            why_msg = "msg_TokenExpired"
        else:
            why_msg = "msg_PostFailed"
            code += 7
            user_rec.verify_email_token = token_entered + "*"  # the key to unlock the e-mail.
            persist_user(user_rec)
            code = 0
            if user_rec.email_verified:
                code = 0

        if code == 0:
            add_msg_success("msgSuccess", ui_db_texts)
        else:
            add_msg_error("msgError", ui_db_texts, task_code + code, why_msg)

        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())
    except Exception as e:
        task_code = task_code + code
        jHtml = get_ups_jHtml("verifySentTokenException", ui_db_texts, task_code, e)

    return jHtml


# eof
