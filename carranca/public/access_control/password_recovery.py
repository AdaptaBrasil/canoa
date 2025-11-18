"""
*Password Recovery*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore wtforms

from flask import render_template, request
import secrets

from ..wtforms import PasswordRecoveryForm
from ...models.public import get_user_where
from ...models.public import persist_user
from ...helpers.email_helper import RecipientsListStr
from ...helpers.sendgrid_helper import send_email
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.ui_db_texts_helper import add_msg_error, add_msg_success, add_msg_final
from ...helpers.route_helper import (
    public_route,
    get_form_input_value,
    init_response_vars,
    is_external_ip_ready,
    get_account_response_data,
    public_route__password_reset,
)


def password_recovery():
    from ...common.app_context_vars import sidekick

    task_code = ModuleErrorCode.ACCESS_CONTROL_PW_RECOVERY.value
    tmpl_rfn, is_get, texts = init_response_vars()
    try:
        task_code += 1  # 1
        form = PasswordRecoveryForm(request.form)
        task_code += 1  # 2
        tmpl_rfn, is_get, texts = get_account_response_data("passwordRecovery")
        task_code += 1  # 3
        requested_email = "" if is_get else get_form_input_value("user_email").lower()
        task_code += 1  # 4
        record_to_update = None if is_get else get_user_where(email=requested_email)

        if is_get:
            pass
        elif record_to_update is None:
            add_msg_error("emailNotRegistered", texts)
        elif not is_external_ip_ready(sidekick.config):
            add_msg_error("noExternalIP", texts)
        else:
            task_code += 1  # 5
            token = secrets.token_urlsafe()
            task_code += 1  # 6
            url = f"http://{sidekick.config.SERVER_EXTERNAL_IP}{sidekick.config.SERVER_EXTERNAL_PORT}{public_route(public_route__password_reset, token= token)}"
            task_code += 1  # 7
            sent_to = RecipientsListStr(requested_email, record_to_update.username)
            send_email(sent_to, "passwordRecovery_email", {"url": url})
            task_code += 1  # 8
            record_to_update.recover_email_token = token
            task_code += 1  # 9
            persist_user(record_to_update, task_code)
            add_msg_success("emailSent", texts)
            task_code = 0
    except Exception as e:  # TODO: log
        msg = add_msg_final("errorPasswordRecovery", texts, task_code)
        sidekick.app_log.error(e)
        sidekick.app_log.debug(msg)

    return render_template(tmpl_rfn, form=form, **texts)


# eof
