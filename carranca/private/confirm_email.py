"""
Tests and confirms that the email and sending functionality
is configured and working correctly.

mgd 2025.10.29 -- 11.08
"""

# cSpell:ignore SMPT

from ..public.ups_handler import get_ups_jHtml
from ..helpers.jinja_helper import process_template
from ..helpers.email_helper import RecipientsDic, RecipientsListStr, send_email
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import ModuleErrorCode
from ..helpers.ui_db_texts_helper import add_msg_success, add_msg_error


def confirm_email(email: str, name: str = "") -> str:

    task_code = ModuleErrorCode.CONFIRM_EMAIL
    jHtml, _, db_texts = init_response_vars()
    try:
        tmpl_rfn, _, db_texts = get_private_response_data("ConfirmEmail")
        task_code += 1
        recipients = RecipientsDic(RecipientsListStr(email, name))
        task_code += 1
        success = send_email(recipients, "confirmEmail", {"user": sidekick.user.username})
        task_code += 1
        if success:
            add_msg_success("emailSentSuccess", db_texts)
        else:
            add_msg_error("emailSentError", db_texts)

        jHtml = process_template(tmpl_rfn, **db_texts.dict())

    except Exception as e:
        jHtml = get_ups_jHtml("emailSentException", db_texts, task_code, e)

    return jHtml


# eof
