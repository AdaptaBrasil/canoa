"""
Tests and confirms that the email and sending functionality
is configured and working correctly.

mgd 2025.10.29 -- 11.08
"""

from ..public.ups_handler import get_ups_jHtml
from ..helpers.jinja_helper import process_template
from ..helpers.email_helper import RecipientsDic, RecipientsListStr
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.gmail_api_helper import send_mail
from ..common.app_error_assistant import ModuleErrorCode
from ..helpers.ui_db_texts_helper import add_msg_success, add_msg_error, add_msg_final


def confirm_email(email: str, name: str = "") -> str:

    task_code = ModuleErrorCode.CONFIRM_EMAIL
    jHtml, _, ui_db_texts = init_response_vars()
    try:
        tmpl_rfn, _, ui_db_texts = get_private_response_data("ConfirmEmail")
        task_code += 1
        recipients = RecipientsDic(RecipientsListStr(email, name))
        task_code += 1
        subject = ui_db_texts["emailSendSubject"]
        task_code += 1
        body = ui_db_texts.format("emailSendBody", (" " if name else "") + name)
        task_code += 1
        success = send_mail(recipients, subject, body)
        task_code += 1
        if success:
            add_msg_success("emailSentSuccess", ui_db_texts)
        else:
            add_msg_error("emailSentError", ui_db_texts)

        jHtml = process_template(tmpl_rfn, **ui_db_texts.dict())

    except Exception as e:
        jHtml = get_ups_jHtml("emailSentException", ui_db_texts, task_code, e)

    return jHtml


# eof
