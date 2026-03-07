"""
Tests and confirms that the email and sending functionality
is configured and working correctly.

mgd 2025.10.29 -- 11.08
"""

# cSpell: ignore  formdata FlaskForm
import random
from flask_wtf import FlaskForm
from ..public.ups_handler import get_ups_jHtml
from ..helpers.types_helper import UsualDict
from ..helpers.jinja_helper import JinjaGeneratedHtml, process_template
from ..helpers.email_helper import RecipientsDic, RecipientsList, send_email
from ..helpers.route_helper import get_private_response_data, init_response_vars, is_method_get
from ..helpers.ui_db_texts_helper import add_msg_success, add_msg_error
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import ModuleErrorCode


def _email_send(
    ui_section: str, email: str, name: str, vars: UsualDict, msg_only: bool, fform: FlaskForm
) -> JinjaGeneratedHtml:

    email_sent = False
    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_CHECK)
    try:
        tmpl_ffn, _, ui_db_texts = get_private_response_data(ui_section)
        task_code += 1
        recipients = RecipientsDic(RecipientsList(email, name))
        task_code += 1

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


def email_test_email(email: str, name: str) -> JinjaGeneratedHtml:

    fform = FlaskForm(formdata=None)
    jHtml = _email_send("emailConfirm", email, name, {}, True, fform)

    return jHtml


def email_send_token(email: str, name: str) -> JinjaGeneratedHtml:
    from .wtforms import EmailTokenForm
    from ..models.public import get_user_where, persist_user

    def __generate_token(digit_count: int) -> int:
        """Generates a random integer with exactly `digit_count` digits."""
        low = 10 ** (digit_count - 1)
        high = (10**digit_count) - 1
        return random.randint(low, high)

    vars: UsualDict = {"user": name}
    if is_method_get():
        token = __generate_token(sidekick.config.email_verify_token_digit_count)
        expiration = sidekick.config.email_verify_token_expires_hours
        vars.update({"expires": expiration, "user": name, "token": token})
        record_to_update = get_user_where(email=email)
        record_to_update.verify_email_sent_at = sidekick.now()
        record_to_update.verify_email_token = str(token)
        persist_user(record_to_update)

    fform = EmailTokenForm()
    jHtml = _email_send("emailVerify", email, name, vars, False, fform)

    return jHtml


def email_verify_token(email: str, name: str) -> JinjaGeneratedHtml:

    fform = FlaskForm(formdata=None)
    jHtml = _email_send("emailConfirm", email, name, {}, True, fform)

    return jHtml


# eof
