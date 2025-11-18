"""
*Change Password*
Part of Private Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore wtforms

from flask import request
from flask_login import current_user

from ..wtforms import ChangePassword
from ...models.public import get_user_where
from ...models.public import persist_user
from ...helpers.py_helper import is_str_none_or_empty
from ...helpers.pw_helper import internal_logout, hash_pass
from ...public.ups_handler import get_ups_jHtml
from ...helpers.jinja_helper import process_template
from ...common.app_context_vars import sidekick
from ...helpers.js_consts_helper import js_form_sec_check
from ...common.app_error_assistant import AppStumbled, ModuleErrorCode
from ...helpers.ui_db_texts_helper import add_msg_error, add_msg_success
from ...helpers.route_helper import (
    redirect_to,
    login_route,
    init_response_vars,
    get_form_input_value,
    get_account_response_data,
)


def do_change_password():
    task_code = ModuleErrorCode.ACCESS_CONTROL_PW_CHANGE.value
    jHtml, is_get, ui_db_texts = init_response_vars()

    try:
        task_code += 1  # 1
        tmpl_rfn, is_get, ui_db_texts = get_account_response_data("passwordChange", "password_reset_or_change")
        password = "" if is_get else get_form_input_value("password")
        task_code += 1  # 2
        confirm_password = "" if is_get else get_form_input_value("confirm_password")
        task_code += 1  # 3
        user = None if is_get else get_user_where(id=current_user.id)
        task_code += 1  # 4
        flask_form = ChangePassword(request.form)

        if is_get:
            pass
        elif not is_str_none_or_empty(msg_error_key := js_form_sec_check()):
            task_code += 1
            msg_error = add_msg_error(msg_error_key, ui_db_texts)
            raise AppStumbled(msg_error, task_code, True, True)
        elif not sidekick.config.DB_len_val_for_pw.check(password):
            task_code += 2
            add_msg_error(
                "invalidPassword",
                ui_db_texts,
                sidekick.config.DB_len_val_for_pw.min,
                sidekick.config.DB_len_val_for_pw.max,
            )
        elif password != confirm_password:
            add_msg_error("passwordsAreDifferent", ui_db_texts)
        elif user is None:
            internal_logout()
            return redirect_to(login_route())
        else:
            task_code += 1  # 5
            user.password = hash_pass(password)
            task_code += 1  # 6
            persist_user(user, task_code)
            task_code += 1  # 7
            add_msg_success("chgPwSuccess", ui_db_texts)
            task_code += 1  # 8
            internal_logout()

        jHtml = process_template(tmpl_rfn, form=flask_form, **ui_db_texts.dict())
    except Exception as e:
        jHtml = get_ups_jHtml("errorPasswordChange", ui_db_texts, task_code, e)

    return jHtml


# eof
