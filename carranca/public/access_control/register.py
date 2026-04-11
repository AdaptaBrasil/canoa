"""
*Register a new user*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore sqlalchemy wtforms

from typing import Any
from flask import request

from ..wtforms import RegisterForm
from ...models.public import User, persist_user
from ...helpers.pw_helper import internal_logout, is_anyone_logged
from ...common.UITextsKeys import UITextsKeys
from ...public.ups_handler import get_ups_jHtml
from ...helpers.jinja_helper import process_template
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.route_helper import (
    get_account_response_data,
    get_form_input_value,
    init_response_vars,
    public_route,
)


def register():

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.ACCESS_CONTROL_REGISTER)

    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_account_response_data("register")
        task_code += 1  # 2
        user_name = "" if is_get else get_form_input_value("username")
        task_code += 1  # 3
        fform = RegisterForm()

        ui_db_texts.set_value(UITextsKeys.Form.submit_route, public_route("register"))

        if is_get and is_anyone_logged():
            internal_logout()
        elif is_get:
            pass
        # post
        elif User.get_where_name_is(user_name):
            ui_db_texts.set_msg_error("userAlreadyRegistered")
        elif User.get_where_email_is(get_form_input_value("email")):
            ui_db_texts.set_msg_error("emailAlreadyRegistered")
        elif not sidekick.config.DB_len_val_for_pw.check(get_form_input_value("password")):
            ui_db_texts.set_msg_error("invalidPasswordLength", (sidekick.config.DB_len_val_for_pw.min, sidekick.config.DB_len_val_for_pw.max))
        elif not sidekick.config.DB_len_val_for_uname.check(user_name):
            ui_db_texts.set_msg_error("invalidUserName", (sidekick.config.DB_len_val_for_uname.min, sidekick.config.DB_len_val_for_uname.max))
        else:
            task_code += 1  # 4
            new_user_rec = User(**request.form)
            task_code += 1  # 5
            persist_user(new_user_rec, task_code)
            task_code += 1  # 6
            ui_db_texts.set_msg_success("welcome")
            # todo welcome e-mail with Token for email confirmation and login after confirmation

        jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("registerException", ui_db_texts, task_code, e)

    return jHtml


# eof
