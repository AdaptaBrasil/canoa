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

from ...models.public import persist_user
from ...helpers.py_helper import is_str_none_or_empty, now_as_iso, to_str
from ...helpers.pw_helper import internal_logout, is_anyone_logged, verify_pass
from ...private.RolesAbbr import RolesAbbr
from ...public.ups_handler import get_ups_jHtml
from ...helpers.jinja_helper import process_template
from ...common.app_context_vars import sidekick
from ...helpers.js_consts_helper import js_form_sec_check
from ...common.app_error_assistant import ModuleErrorCode, AppStumbled
from ...helpers.ui_db_texts_class import add_msg_error, add_msg_warning
from ...helpers.route_helper import (
    home_route,
    redirect_to,
    init_response_vars,
    get_form_input_value,
    get_account_response_data,
)
from ...models.public import User, get_user_role_abbr


def do_login():

    from ..wtforms import LoginForm

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.ACCESS_CONTROL_LOGIN)
    fform = LoginForm()

    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_account_response_data("login")
        task_code += 1  # 2
        if is_get and is_anyone_logged():
            task_code += 1  # 3
            internal_logout()
        elif is_get:
            task_code += 2  # 4
            pass
        elif not is_str_none_or_empty(msg_error_key := js_form_sec_check()):
            task_code += 3  # 5
            msg_error = add_msg_error(msg_error_key, ui_db_texts)
            raise AppStumbled(msg_error, task_code, True, True)
        else:
            task_code += 4  # 6
            username = get_form_input_value("username")  # TODO tmpl_form
            task_code += 1  # 7
            password = get_form_input_value("password")
            task_code += 1  # 8
            search_for = to_str(username).lower()
            task_code += 1  # 9
            user = User.get_where(username_lower=search_for)  # by uname
            task_code += 1  # 10
            user = User.get_where(email=search_for) if user is None else user  # or by email
            user_role_abbr = None if user is None else get_user_role_abbr(user.id, user.id_role)
            task_code += 1  # 11
            if not user:
                task_code += 1  # 12
                add_msg_error("userOrPwdIsWrong", ui_db_texts)
            elif not verify_pass(password, user.password):
                # TODO: new  user.login_failed = True
                user.password_failed_at = func.now()
                task_code += 2  # 13
                user.password_failures = user.password_failures + 1
                add_msg_error("userOrPwdIsWrong", ui_db_texts)
                persist_user(user, task_code)
                # persist_user creates an Anonymous User, so lets logout it
            elif user.disabled:
                task_code += 3  # 14
                add_msg_error("userIsDisabled", ui_db_texts)
            elif user_role_abbr is None:
                task_code += 4  # 15
                add_msg_error("roleNotFound", ui_db_texts, "(null)")
            elif not user_role_abbr in {role.value for role in RolesAbbr}:
                task_code += 5  # 16
                add_msg_error("roleNotFound", ui_db_texts, user_role_abbr)
            else:
                task_code += 6  # 17
                user_email_verified = user.email_verified
                task_code += 1  # 18
                # TODO: new  user.login_failed = False
                user.recover_email_token = None
                user.last_login_at = func.now()
                user.password_failures = 0
                task_code += 1  # 19
                remember_me = not is_str_none_or_empty(request.form.get("remember_me"))
                task_code += 1  # 20
                login_user(user, remember_me)
                task_code += 1  # 21
                msg = f"{user.username} [id: {user.id}, role: '{user.role.name}'] just logged in [{now_as_iso()}]."
                sidekick.display.info(msg)
                # user obj is lost here
                task_code += 1  # 22
                persist_user(user, task_code)
                # for this login work, User must inherited from SQLAlchemy.Model
                task_code += 1  # 23
                if user_email_verified:
                    return redirect_to(home_route())

                task_code += 1  # 24
                add_msg_warning("msgVerifyEmail", ui_db_texts)
                ui_db_texts["display_footer"] = "False"
                ui_db_texts.display_msg_only = True

        jHtml = process_template(
            tmpl_ffn,
            form=fform,
            **ui_db_texts.data(),
        )
    except Exception as e:
        jHtml = get_ups_jHtml("loginException", ui_db_texts, task_code, e)
        logout_user()  # 2025.03.10

    return jHtml


# eof
