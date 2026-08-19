"""
*Register a new user*
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore sqlalchemy wtforms

from flask import request

from ..wtforms import RegisterForm
from ...models.public.user import User
from ...config.FormIcons import FormIcons as fi
from ...helpers.pw_helper import internal_logout, is_anyone_logged
from ...helpers.py_helper import generate_random, is_str_none_or_empty
from ...helpers.email_helper import RecipientsDic, RecipientsList, send_email
from ...helpers.js_consts_helper import js_form_sec_check
from ...common.ups_handler import get_ups_jHtml
from ...helpers.jinja_helper import process_template
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.route_helper import (
    get_account_response_data,
    get_form_input_value,
    init_response_vars,
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
        ui_db_texts.set_value("display_footer", "True")

        if is_get and is_anyone_logged():
            internal_logout()
        elif is_get:
            pass
        # else post
        elif User.get_where_name_is(user_name):
            ui_db_texts.set_msg_error("userAlreadyRegistered")
        elif User.get_where_email_is(get_form_input_value("email")):
            ui_db_texts.set_msg_error("emailAlreadyRegistered")
        elif not sidekick.config.DB_len_val_for_pw.check(get_form_input_value("password")):
            ui_db_texts.set_msg_error("invalidPasswordLength", (sidekick.config.DB_len_val_for_pw.min, sidekick.config.DB_len_val_for_pw.max))
        elif not sidekick.config.DB_len_val_for_uname.check(user_name):
            ui_db_texts.set_msg_error("invalidUserName", (sidekick.config.DB_len_val_for_uname.min, sidekick.config.DB_len_val_for_uname.max))
        elif not is_str_none_or_empty(msg_error_key := js_form_sec_check(expect_authenticated=False)):
            ui_db_texts.set_msg_error(msg_error_key)
        else:
            email_sent = False
            task_code += 1  # 4
            new_user_rec = User(**request.form)
            task_code += 1  # 5
            # Refs GH #1: welcome e-mail with a token for email confirmation.
            token = generate_random(sidekick.config.EMAIL_VERIFY_TOKEN_DIGIT_COUNT)
            task_code += 1  # 6
            new_user_rec.verify_email_token = str(token)
            task_code += 1  # 7
            User.set_row(new_user_rec)
            ui_db_texts.set_msg_success("welcome")
            ui_db_texts.set_value("display_footer", "False")
            task_code += 1  # 8

            # same mechanism as password_recovery.py: subject/content/text live in the
            # already-loaded "register" ui_items section, DB-driven like every other UI text.
            try:
                recipients = RecipientsDic(RecipientsList(new_user_rec.email, user_name))
                email_vars = {
                    "user": user_name,
                    "token": token,
                    "expires": sidekick.config.EMAIL_VERIFY_TOKEN_EXPIRES_HOURS,
                }
                email_sent = send_email(recipients, ui_db_texts.section, email_vars)
            except Exception as email_err:
                email_sent = False
                sidekick.display.error(f"Welcome email failed for {new_user_rec.email}: {email_err}")

            if email_sent:
                ui_db_texts.set_msg_success("welcome_and_verify" if email_sent else "welcome")
            else:
                ui_db_texts.set_msg_success("welcome")
                new_user_rec.verify_email_token = None
                User.set_row(new_user_rec)

        jHtml = process_template(tmpl_ffn, form=fform, fi=fi.with_icon("register"), **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("registerException", ui_db_texts, task_code, e)

    return jHtml


# eof
