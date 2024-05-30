# Equipe da Canoa -- 2024
# public\login.py
#
# mgd
# cSpell:ignore tmpl sqlalchemy
"""
    *Register*
    Part of Public Authentication Processes
"""
from flask import render_template, request
from typing import Any
from carranca import db

from ..helpers.texts_helper import add_msg_success, add_msg_error
from ..helpers.route_helper import get_account_form_data, get_input_text, public_route

from .forms import RegisterForm
from .models import Users

def do_register():
    def __exists_user_that(**kwargs: Any) -> bool:
        user= Users.query.filter_by(**kwargs).first()
        return user is not None

    template, is_get, texts = get_account_form_data('register')
    tmpl_form= RegisterForm(request.form)

    if is_get: # is_post
        pass

    elif __exists_user_that(username_lower = get_input_text('username').lower()):
        add_msg_error('userAlreadyRegistered', texts) if user else ''

    elif __exists_user_that(email = get_input_text('email').lower()).first():
        add_msg_error('emailAlreadyRegistered', texts) if user else ''

    else:
        try:
            user= Users(**request.form, disabled = False)
            db.session.add(user)
            db.session.commit()
            add_msg_success('welcome', texts)
        except Exception as e:
            add_msg_error('registerError', texts) if user else ''
            # TODO Log

    return render_template(
        template,
        form=tmpl_form,
        public_route= public_route,
        **texts
    )
#eof