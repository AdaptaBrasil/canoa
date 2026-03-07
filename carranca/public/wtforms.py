"""
*wtforms* HTML forms
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd 2024-04-09,27; 06-22
"""

# cSpell:ignore: wtforms


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import Email, InputRequired, Length

from ..helpers.wtf_helper import LenValidate
from ..common.app_context_vars import sidekick

# Public forms
# -------------------------------------------------------------
# Text here has no relevance, the ui_text table is actually used.

max_name = LenValidate(
    min(sidekick.config.DB_len_val_for_uname.min, sidekick.config.DB_len_val_for_email.min),
    max(sidekick.config.DB_len_val_for_uname.max, sidekick.config.DB_len_val_for_email.max),
)


class LoginForm(FlaskForm):
    username = StringField(
        "",
        validators=[InputRequired(), Length(**max_name.wtf_val())],
        render_kw={"class": "form-control", "autofocus": "true"},
    )
    password = PasswordField(
        "",
        validators=[InputRequired(), Length(**sidekick.config.DB_len_val_for_pw.wtf_val())],
        render_kw={"class": "form-control"},
    )
    remember_me = BooleanField(
        "",
        render_kw={"class": "form-check-btn"},
    )


class RegisterForm(FlaskForm):
    username = StringField(
        "",
        validators=[InputRequired(), Length(**max_name.wtf_val())],
        render_kw={"class": "form-control", "autofocus": "true"},
    )
    email = StringField(
        "",
        validators=[
            InputRequired(),
            Email(),
            Length(**sidekick.config.DB_len_val_for_email.wtf_val()),
        ],
    )
    password = PasswordField(
        "",
        validators=[InputRequired(), Length(**sidekick.config.DB_len_val_for_pw.wtf_val())],
        render_kw={"class": "form-control"},
    )
    disabled = BooleanField("Disabled")


class PasswordRecoveryForm(FlaskForm):
    user_email = StringField(
        "",
        validators=[InputRequired(), Email()],
        render_kw={"class": "form-control", "autofocus": "true"},
    )


# eof
