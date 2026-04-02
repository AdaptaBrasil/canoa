"""
*Change Password*
Part of Private Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore wtforms

from flask_login import current_user

from ..wtforms import ChangePassword
from ...models.public import get_user_where
from ...models.public import persist_user
from ...helpers.py_helper import is_str_none_or_empty
from ...helpers.pw_helper import internal_logout, hash_password, verify_password
from ...public.ups_handler import get_ups_jHtml
from ...helpers.jinja_helper import process_template
from ...helpers.types_helper import Jinja_Rendered, Flask_Response
from ...common.app_context_vars import sidekick
from ...helpers.js_consts_helper import js_form_sec_check
from ...common.app_error_assistant import AppStumbled, ModuleErrorCode
from ...helpers.ui_db_texts_manager import set_msg_error, set_msg_warn, MSG_DEFAULT
from ...helpers.route_helper import (
    redirect_to,
    login_route,
    init_response_vars,
    get_form_input_value,
    get_account_response_data,
)


def password_change() -> Jinja_Rendered | Flask_Response:
    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.ACCESS_CONTROL_PW_CHANGE)
    fform = ChangePassword()

    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_account_response_data("passwordChange", "password_reset_or_change")
        current_password = "" if is_get else get_form_input_value(fform.current_password.name)
        task_code += 1  # 2
        password = "" if is_get else get_form_input_value(fform.password.name)
        task_code += 1  # 3
        confirm_password = "" if is_get else get_form_input_value(fform.confirm_password.name)
        task_code += 1  # 4
        user_rec = None if is_get else get_user_where(id=current_user.id)
        task_code += 1  # 5

        if is_get:
            pass
        elif not is_str_none_or_empty(msg_error_key := js_form_sec_check()):
            task_code += 1  # 6
            msg_error = set_msg_error(msg_error_key, ui_db_texts)
            raise AppStumbled(msg_error, task_code, True, True)
        elif not sidekick.config.DB_len_val_for_pw.check(password):
            task_code += 2  # 7
            ui_db_texts.set_msg_warn("invalidPasswordLength", sidekick.config.DB_len_val_for_pw.min, sidekick.config.DB_len_val_for_pw.max)
        elif password != confirm_password:
            ui_db_texts.set_msg_warn("passwordsAreDifferent")
        elif user_rec is None:
            internal_logout()
            return redirect_to(login_route())
        elif not verify_password(current_password, user_rec.password):
            ui_db_texts.set_msg_error("passwordWrong")
        elif verify_password(password, user_rec.password):
            ui_db_texts.set_msg_warn("passwordsAreEqual")
        else:
            task_code += 1  # 6
            user_rec.password = hash_password(password)
            task_code += 1  # 7
            persist_user(user_rec, task_code)
            task_code += 1  # 8
            ui_db_texts.set_msg_success()
            task_code += 1  # 9
            internal_logout()

        jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())
    except Exception as e:
        jHtml = get_ups_jHtml("passwordChangeException", ui_db_texts, task_code, e)

    return jHtml


# eof
