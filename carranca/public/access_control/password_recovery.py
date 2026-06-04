"""
*Password Recovery*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore wtforms

import secrets

from datetime import timedelta, datetime

from ..wtforms import PasswordRecoveryForm
from ...models.public import get_user_where, User
from ...models.public import persist_user
from ...config.FormIcons import FormIcons as fi
from ...helpers.py_helper import elapsed_hours
from ...common.UITextsKeys import UITextsKeys
from ...public.ups_handler import get_ups_jHtml
from ...helpers.email_helper import RecipientsList, RecipientsDic, send_email
from ...helpers.jinja_helper import process_template
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.ui_db_texts_manager import set_msg_fatal
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
        task_code += 1  # 2
        fform = PasswordRecoveryForm()
        requested_email = "" if is_get else get_form_input_value(fform.user_email.name).lower()
        task_code += 1  # 3
        user_rec = None if is_get else get_user_where(email=requested_email)
        task_code += 1  # 4
        expires_in_hours = sidekick.config.EMAIL_RECOVER_TOKEN_EXPIRES_HOURS

        def __can_request_password_recovery() -> int:
            def __user_is_in_recovery_process(record_to_update, check_state: bool) -> bool:
                if not record_to_update.recover_email_token:
                    return False

                start_time: datetime | None = record_to_update.recover_email_token_at
                if start_time is None:
                    return check_state  # token exists but no timestamp — treat as in-progress

                # 1 day expiration time for the token, but it can be configured in the future
                expiration_time = start_time + timedelta(days=1)
                return expiration_time > sidekick.now()

            code = 0
            if user_rec is None:
                code = 12
            elif user_rec.disabled:
                code = 23  # how did the user is logged?
            elif user_rec.password is None:
                code = 34  # strange, better to avoid sending email if user has no password set
            elif __user_is_in_recovery_process(user_rec, True):
                code = 45  # invalid process state,
            elif __user_is_in_recovery_process(user_rec, False):
                code = 56  # user is already in a recovery process, better to avoid sending another email and creating confusion.
            elif not user_rec.email_verified:
                code = 67  # who knows where the email goes.
            return code

        def __has_active_token(emitted_at: datetime | None):
            # User has a valid token, ask to wait
            return elapsed_hours(emitted_at) < expires_in_hours if emitted_at else False

        def __save_token(token: str, user_rec: User, task_code: int) -> int:
            code = 10
            user_rec.recover_email_token = token
            code += 1
            persist_user(user_rec, task_code)
            code = 0
            return code

        if is_get:
            ui_db_texts.set_msg_info()
            task_code += 1  # 5
        elif user_rec is None:
            task_code += 2  # 6
            set_msg_fatal("emailNotRegistered", ui_db_texts)
        elif __has_active_token(user_rec.recover_email_token_at):
            task_code += 3  # 7
            text_expiry = ui_db_texts.get_ui_datetime(expires_in_hours, user_rec.recover_email_token_at)
            ui_db_texts.set_msg_warn("hasActiveToken", text_expiry)
            ui_db_texts.display_msg_only = True
        elif not is_external_ip_ready(sidekick.config):
            task_code += 4  # 8
            set_msg_fatal("noExternalIP", ui_db_texts)
        elif (code := __can_request_password_recovery()) > 0:
            task_code += 5  # 9
            set_msg_fatal("cannotRequestPwRecovery", ui_db_texts, code)
        elif (user_name := user_rec.username) is None:
            # save user_name, before saving record (after saving, cannot be read)
            task_code += 6  # 10
            set_msg_fatal("cannotSaveToken", ui_db_texts, 1)
        elif (token := secrets.token_urlsafe()) is None:
            task_code += 7  # 11
            set_msg_fatal("cannotSaveToken", ui_db_texts, 2)
        elif (code := __save_token(token, user_rec, task_code=+8)) > 0:  # 10
            set_msg_fatal("cannotSaveToken", ui_db_texts, code)
        else:
            task_code += 9  # 12
            route_me = public_route(public_route__password_reset, token=token)
            task_code += 1
            url = f"{sidekick.config.SERVER_EXTERNAL_SCHEME}://{sidekick.config.SERVER_EXTERNAL_IP}{sidekick.config.SERVER_EXTERNAL_PORT}{route_me}"
            task_code += 1  # 13
            recipients = RecipientsDic(RecipientsList(requested_email, user_name))
            task_code += 1  # 14
            send_email(recipients, ui_db_texts.section, {"user": user_name, "url": url})
            task_code += 1  # 15
            key, msg = ui_db_texts.set_msg_success()
            ui_db_texts.set_ui_datetime(key, msg, expires_in_hours)
            ui_db_texts.replace(UITextsKeys.Form.btn_submit, "successButton")

        jHtml = process_template(tmpl_ffn, form=fform, fi=fi.with_icon("email"), **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("emailSentException", ui_db_texts, task_code, e)

    return jHtml


# eof
