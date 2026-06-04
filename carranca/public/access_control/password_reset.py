"""
*Reset Password*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore wtforms passwordreset
from datetime import datetime
from ...models.public import persist_user, get_user_where
from ...config.FormIcons import FormIcons as fi
from ...private.wtforms import ChangePassword
from ...public.ups_handler import get_ups_jHtml
from ...helpers.pw_helper import hash_password
from ...helpers.py_helper import elapsed_hours, to_str
from ...helpers.jinja_helper import process_template
from ...helpers.route_helper import get_form_input_value, init_response_vars, get_account_response_data
from ...common.app_error_assistant import ModuleErrorCode


def password_reset(token):
    from ...common.app_context_vars import sidekick

    def __is_token_valid(time_stamp: datetime, max: int) -> bool:
        hours = elapsed_hours(datetime.now(), time_stamp)
        return 0 <= hours <= max

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.ACCESS_CONTROL_PW_RESET)
    fform = ChangePassword()
    # TODO test, fake form?

    try:
        task_code += 1  # 1
        jHtml, is_get, ui_db_texts = get_account_response_data("passwordReset", "password_reset_or_change")
        token_str = to_str(token)
        password = "" if is_get else get_form_input_value("password")
        task_code += 1  # 2
        confirm_password = "" if is_get else get_form_input_value("confirm_password")

        # If you need the password pwd=  hash_pass(password);
        task_code += 1  # 3
        if len(token_str) < 12:
            ui_db_texts.set_msg_error("invalidToken")
        elif is_get:
            pass
        elif not sidekick.config.DB_len_val_for_pw.check(password):
            ui_db_texts.set_msg_warn("invalidPasswordLength", (sidekick.config.DB_len_val_for_pw.min, sidekick.config.DB_len_val_for_pw.max))
        elif password != confirm_password:
            ui_db_texts.set_msg_error("passwordsAreDifferent")
        elif (record_to_update := get_user_where(recover_email_token=token_str)) is None:
            ui_db_texts.set_msg_fatal("invalidToken")
        elif not __is_token_valid(record_to_update.recover_email_token_at, 5):
            ui_db_texts.set_msg_fatal("expiredToken")
        else:
            task_code += 1  # 4
            record_to_update.password = hash_password(password)
            record_to_update.recover_email_token = None
            task_code += 1  # 5
            persist_user(record_to_update, task_code)
            ui_db_texts.set_msg_success()

        jHtml = process_template(jHtml, form=fform, fi=fi.with_icon("password_change"), **ui_db_texts.data())
    except Exception as e:
        jHtml = get_ups_jHtml("msgException", ui_db_texts, task_code, e)

    return jHtml


# eof
