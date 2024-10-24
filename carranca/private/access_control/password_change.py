"""
    *Change Password*
    Part of Private Access Control Processes

    Equipe da Canoa -- 2024
    mgd
"""
# cSpell:ignore tmpl wtforms

from flask import render_template, request
from flask_login import current_user

from ...public.models import persist_user
from ...helpers.pw_helper import internal_logout, hash_pass
from ...helpers.error_helper import ModuleErrorCode
from ...helpers.ui_texts_helper import add_msg_error, add_msg_success
from ...helpers.route_helper import (
    redirect_to,
    login_route,
    init_form_vars,
    get_input_text,
    get_account_form_data,
)
from ...public.models import get_user_where
from ...Sidekick import sidekick
from ..wtforms import ChangePassword


def do_password_change():
    task_code = ModuleErrorCode.ACCESS_CONTROL_PW_CHANGE.value
    tmpl_form, template, is_get, texts = init_form_vars()
    # TODO test, fake form?

    try:
        task_code += 1  # 1
        template, is_get, texts = get_account_form_data('passwordChange', 'password_reset_or_change')
        password = '' if is_get else get_input_text('password')
        task_code += 1  # 2
        confirm_password = '' if is_get else get_input_text('confirm_password')
        task_code += 1  # 3
        user =  None if is_get else get_user_where(id=current_user.id)
        task_code += 1  # 4
        tmpl_form = ChangePassword(request.form)

        if is_get:
            pass
        elif not sidekick.config.len_val_for_pw.check(password):
            add_msg_error('invalidPassword', texts, sidekick.config.len_val_for_pw.min, sidekick.config.len_val_for_pw.max)
        elif password != confirm_password:
            add_msg_error('passwordsAreDifferent', texts)
        elif user is None:
            internal_logout()
            return redirect_to(login_route())
        else:
            task_code += 1  # 5
            user.password = hash_pass(password)
            task_code += 1  # 6
            persist_user(user, task_code)
            task_code += 1  # 7
            add_msg_success('chgPwSuccess', texts)
            task_code += 1  # 8
            internal_logout()

    except Exception as e:
        msg = add_msg_error('errorPasswordChange', texts, task_code)
        print(f"{e} - {msg}")

    return render_template(
        template,
        form=tmpl_form,
        **texts,
    )


# eof
