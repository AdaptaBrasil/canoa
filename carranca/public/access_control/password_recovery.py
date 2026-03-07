"""
*Password Recovery*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore wtforms

import secrets

from flask import request
from datetime import timedelta, datetime

from ..wtforms import PasswordRecoveryForm
from ...models.public import get_user_where
from ...models.public import persist_user
from ...helpers.py_helper import is_str_none_or_empty
from ...public.ups_handler import get_ups_jHtml
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

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.ACCESS_CONTROL_PW_RECOVERY)

    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_account_response_data("passwordRecovery")
        requested_email = "" if is_get else get_form_input_value("user_email").lower()
        task_code += 1  # 2
        user_data = None if is_get else get_user_where(email=requested_email)
        task_code += 1  # 3
        fform = PasswordRecoveryForm()
        task_code += 1  # 4

        def __can_request_password_recovery() -> int:
            def __user_is_in_recovery_process(record_to_update, check_state: bool) -> bool:
                if is_str_none_or_empty(record_to_update.recover_email_token):
                    return False

                start_time: datetime | None = record_to_update.recover_email_token_at
                if start_time is None:
                    return check_state  # token exists but no timestamp — treat as in-progress

                # 1 day expiration time for the token, but it can be configured in the future
                expiration_time = start_time + timedelta(days=1)
                return expiration_time > sidekick.now()

            code = 0
            if user_data is None:
                code = 12
            elif user_data.disabled:
                code = 23
            elif user_data.password is None:
                code = 34  # strange, better to avoid sending email if user has no password set
            elif __user_is_in_recovery_process(user_data, True):
                code = 45  # invalid process state,
            elif __user_is_in_recovery_process(user_data, False):
                code = 56  # user is already in a recovery process, better to avoid sending another email and creating confusion.
            elif not user_data.email_confirmed:
                code = 67  # who knows where the email goes.
            return code

        if is_get:
            task_code += 1  # 5
            pass
        elif user_data is None:
            task_code += 2  # 6
            add_msg_error("emailNotRegistered", ui_db_texts)
        elif not is_external_ip_ready(sidekick.config):
            task_code += 3  # 7
            add_msg_error("noExternalIP", ui_db_texts)
        elif (code := __can_request_password_recovery()) > 0:
            task_code += 4  # 8
            add_msg_error("cannotRequestPwRecovery", ui_db_texts, code)
            ui_db_texts.display_msg_only = True
        else:
            task_code += 4  # 8
            token = secrets.token_urlsafe()
            task_code += 1  # 10
            url = f"http://{sidekick.config.SERVER_EXTERNAL_IP}{sidekick.config.SERVER_EXTERNAL_PORT}{public_route(public_route__password_reset, token= token)}"
            task_code += 1  # 11
            sent_to = RecipientsList(requested_email, user_data.username)
            send_email(sent_to, "passwordRecovery_email", {"url": url})
            task_code += 1  # 12
            user_data.recover_email_token = token
            task_code += 1  # 13
            persist_user(user_data, task_code)
            add_msg_success("emailSent", ui_db_texts)
            task_code = 0

        jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("pwRecoveryEmailSentException", ui_db_texts, task_code, e)

    return jHtml


# eof
