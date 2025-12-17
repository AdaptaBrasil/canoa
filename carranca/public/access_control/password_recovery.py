"""
*Password Recovery*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore wtforms

from flask import request
import secrets

from ..wtforms import PasswordRecoveryForm
from ...models.public import get_user_where
from ...models.public import persist_user
from ...helpers.email_helper import RecipientsList, send_email
from ...helpers.jinja_helper import process_template
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

    tmpl_ffn, is_get, ui_db_texts, task_code = init_response_vars(
        ModuleErrorCode.ACCESS_CONTROL_PW_RECOVERY
    )
    fform = PasswordRecoveryForm()

    try:
        task_code += 1  # 1
        task_code += 1  # 2
        tmpl_ffn, is_get, ui_db_texts = get_account_response_data("passwordRecovery")
        task_code += 1  # 3
        requested_email = "" if is_get else get_form_input_value("user_email").lower()
        task_code += 1  # 4
        record_to_update = None if is_get else get_user_where(email=requested_email)

        if is_get:
            pass
        elif record_to_update is None:
            add_msg_error("emailNotRegistered", ui_db_texts)
        elif not is_external_ip_ready(sidekick.config):
            add_msg_error("noExternalIP", ui_db_texts)
        else:
            task_code += 1  # 5
            token = secrets.token_urlsafe()
            task_code += 1  # 6
            url = f"http://{sidekick.config.SERVER_EXTERNAL_IP}{sidekick.config.SERVER_EXTERNAL_PORT}{public_route(public_route__password_reset, token= token)}"
            task_code += 1  # 7
            sent_to = RecipientsList(requested_email, record_to_update.username)
            send_email(sent_to, "passwordRecovery_email", {"url": url})
            task_code += 1  # 8
            record_to_update.recover_email_token = token
            task_code += 1  # 9
            persist_user(record_to_update, task_code)
            add_msg_success("emailSent", ui_db_texts)
            task_code = 0
    except Exception as e:  # TODO: log
        msg = add_msg_final("errorPasswordRecovery", ui_db_texts, task_code)
        sidekick.display.debug(msg)
        sidekick.display.error(e)

    return process_template(tmpl_ffn, form=fform, **ui_db_texts.dict())


# eof
