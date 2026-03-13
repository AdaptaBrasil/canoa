"""
Sends a validation token to confirm that the user has access
to the provided email

mgd 2026.01.11
"""

# cSpell:ignore SMPT

from ..public.ups_handler import get_ups_jHtml
from ..helpers.jinja_helper import process_template
from ..helpers.email_helper import RecipientsDic, RecipientsList, send_email
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import ModuleErrorCode
from ..helpers.ui_db_texts_class import add_msg_success, add_msg_error


def send_token_and_verify(email: str, name: str = "") -> str:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.EMAIL_CHECK)
    try:
        ui_section = "sendTokenAndVerify"
        task_code += 1
        tmpl_ffn, _, ui_db_texts = get_private_response_data(ui_section)
        task_code += 1
        recipients = RecipientsDic(RecipientsList(email, name))
        task_code += 1
        success = send_email(recipients, ui_section, {"user": sidekick.user.username})
        task_code += 1
        if success:
            add_msg_success("emailSentSuccess", ui_db_texts)
        else:
            add_msg_error("emailSentError", ui_db_texts)

        task_code += 1
        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("emailSentException", ui_db_texts, task_code, e)

    return jHtml


# eof
