"""
*Login*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore sqlalchemy wtforms

from flask import request
from sqlalchemy import func
from flask_login import login_user, logout_user

from ..wtforms import LoginForm
from ...models.public import User, persist_user
from ...helpers.py_helper import is_str_none_or_empty, now_as_iso
from ...helpers.pw_helper import internal_logout, is_anyone_logged, verify_password
from ...private.RolesAbbr import RolesAbbr
from ...public.ups_handler import get_ups_jHtml
from ...helpers.jinja_helper import process_template
from ...common.app_context_vars import sidekick
from ...helpers.js_consts_helper import js_form_sec_check
from ...common.app_error_assistant import ModuleErrorCode, AppStumbled
from ...helpers.route_helper import (
    home_route,
    redirect_to,
    init_response_vars,
    get_form_input_value,
    get_account_response_data,
)


def do_login():

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.ACCESS_CONTROL_LOGIN)

    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_account_response_data("login")
        task_code += 1  # 2
        fform = LoginForm()

        if is_get and is_anyone_logged():
            task_code += 1  # 3
            internal_logout()
        elif is_get:
            task_code += 2  # 4
            pass
        elif not is_str_none_or_empty(msg_error_key := js_form_sec_check()):
            task_code += 3  # 5
            _, msg_error = ui_db_texts.set_msg_error(msg_error_key)
            raise AppStumbled(msg_error, task_code, True, True)
        else:
            task_code += 4  # 6
            # user can inform name OR email => id
            id = get_form_input_value("username")
            task_code += 1  # 7
            password = get_form_input_value("password")
            task_code += 1  # 8
            user = User.get_where_name_is(id)
            task_code += 1  # 9
            user = User.get_where_email_is(id) if user is None else user  # or by email
            task_code += 1  # 10
            if not user:
                task_code += 1  # 12
                ui_db_texts.set_msg_error("userOrPwdIsWrong")
            elif not verify_password(password, user.password):
                # TODO: new  user.login_failed = True
                user.password_failed_at = func.now()
                task_code += 2  # 13
                user.password_failures = user.password_failures + 1
                ui_db_texts.set_msg_error("userOrPwdIsWrong")
                persist_user(user, task_code)
            elif user.disabled:
                task_code += 3  # 14
                ui_db_texts.set_msg_error("userIsDisabled")
            elif not user.role.abbr in RolesAbbr:
                task_code += 5  # 16
                ui_db_texts.set_msg_error("roleNotFound", user.role.abbr)
            else:
                task_code += 6  # 17
                user_email_verified = user.email_verified
                task_code += 1  # 18
                # start
                # reset the 'user state'
                user.recover_email_token = None
                user.last_login_at = func.now()
                user.password_failures = 0
                # end
                task_code += 1  # 19
                remember_me = not is_str_none_or_empty(request.form.get("remember_me"))
                task_code += 1  # 20
                login_user(user, remember_me)
                task_code += 1  # 21
                msg = f"{user.username} [id: {user.id}, role: '{user.role.name}'] just logged in [{now_as_iso()}]."
                sidekick.display.info(msg)
                task_code += 1  # 22
                # user obj is `lost` here
                persist_user(user, task_code)
                task_code += 1  # 23
                if user_email_verified:
                    return redirect_to(home_route())

                task_code += 1  # 24
                ui_db_texts.set_msg_warn("msgVerifyEmail")
                ui_db_texts.set_value("display_footer", "False")
                ui_db_texts.display_msg_only = True

        jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("loginException", ui_db_texts, task_code, e)
        logout_user()  # 2025.03.10

    return jHtml


# eof
