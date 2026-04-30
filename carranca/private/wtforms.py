"""
*wtforms* HTML forms
Part of Private Access Control & `File Validation` Processes

Equipe da Canoa -- 2024
mgd 2024-04-09,27; 06-22, 2026-01
"""

# cSpell:ignore: wtforms urlname iconfilename uploadfile tmpl RRGGBB gpkg attribs

from flask_wtf import FlaskForm
from wtforms import (
    FileField,
    StringField,
    SelectField,
    BooleanField,
    IntegerField,
    TextAreaField,
    PasswordField,
)
from wtforms.validators import NumberRange, InputRequired, DataRequired, Length, URL

from ..common.app_context_vars import sidekick

# -------------------------------------------------------------
# Text here has no relevance, the ui_text table is actually used.


class EmptyForm(FlaskForm):
    """
    Empty form class used for:
        Variable initialization of forms
        CSRF (Cross-Site Request Forgery) protection.

    This form contains no fields and serves only to validate CSRF tokens,
    ensuring that state-changing requests originate from the application itself
    and not from external sources.
    """

    # This is an empty form for CSRF protection only
    pass


# _ ⚠️ _________________________________________________
#  Keep "name" and "id" the same string
#  or don't specified "id"
#
#  Because {{ schema_sep.id }} will render the name
#  But {{ schema_sep.render_kw.id }} will write the id.
# ________________________________________________________


# Private form
class EmailTokenForm(FlaskForm):
    x = sidekick.config.EMAIL_VERIFY_TOKEN_DIGIT_COUNT
    min = int("1" + "0" * (x - 1))  # e.g., 100000 for 6 digits
    max = int("9" * x)  # e.g., 999999 for 6 digits
    token = IntegerField(
        "",
        validators=[DataRequired(), NumberRange(min=min, max=max)],
        render_kw={"class": "form-control"},
    )


# Private form
class ReceiveFileForm(FlaskForm):
    schema_sep = SelectField("", validators=[DataRequired()], render_kw={"class": "form-select"})
    uploadfile = FileField("", render_kw={"class": "form-control", "accept": ".zip"})
    urlname = StringField("", validators=[URL()], render_kw={"class": "form-control"})


# Private & Public form
class ChangePassword(FlaskForm):
    current_password = PasswordField(
        "",
        validators=[
            InputRequired(),
            Length(**sidekick.config.DB_len_val_for_pw.wtf_val()),
        ],
        render_kw={"class": "form-control"},
    )

    password = PasswordField(
        "",
        validators=[
            InputRequired(),
            Length(**sidekick.config.DB_len_val_for_pw.wtf_val()),
        ],
        render_kw={"class": "form-control"},
    )

    confirm_password = PasswordField(
        "",
        validators=[
            InputRequired(),
            Length(**sidekick.config.DB_len_val_for_pw.wtf_val()),
        ],
        render_kw={"class": "form-control"},
    )


# Private form
class SepEdit(FlaskForm):
    """
    ------------------------------------------------------------
       ⚠️
        Don't defined here mutable render_kw, they persist
        set value to those that will not change throw tha app
        see:
            carranca/private/sep_new_edit.py
                fform = SepNew(request.form) if is_new
                        else
                        SepEdit(request.form)
    ------------------------------------------------------------
        like:
          lang, disabled, readonly, required
    """

    manager_name = SelectField(
        "",
        render_kw={"class": "form-control", "disabled": True},  # almost
    )

    schema_name = StringField(
        "",
        validators=[Length(min=5, max=140)],  # TODO sidekick.config.DB_len_val_for_sep
        render_kw={"class": "form-control", "disabled": True},  # almost always disabled
    )

    sep_name = StringField(
        "",
        validators=[Length(min=5, max=140)],  # TODO sidekick.config.DB_len_val_for_sep
        render_kw={
            "class": "form-control",
            "autofocus": "true",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",
        },
    )

    description = StringField(
        "",
        validators=[InputRequired(), Length(min=5, max=140)],
        render_kw={
            "class": "form-control",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",  # ⚠️ Don't defined here, they persist. See below SepNew
        },
    )

    icon_file = FileField("", render_kw={"class": "form-control", "accept": ".svg"})

    # class is special for bootstrap (the only checkbox in Canoa): frm-check-for-bs
    visible = BooleanField("")


# Derived Private form
class SepNew(SepEdit):

    manager_list = SelectField(
        "",
        validators=[DataRequired()],
        coerce=int,
        render_kw={"class": "form-select"},
    )

    schema_list = SelectField(
        "",
        validators=[DataRequired()],
        coerce=int,
        render_kw={"class": "form-select"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.manager_list.validators.append(InputRequired())
        self.schema_list.validators.append(InputRequired())


# Private form
class ScmEdit(FlaskForm):
    """
    ------------------------------------------------------------
       ⚠️
        Don't defined here mutable render_kw, they persist
        set value to those that will not change throw tha app
        see:
            carranca/private/sep_new_edit.py
                fform = SepNew(request.form) if is_new
                        else
                        SepEdit(request.form)
    ------------------------------------------------------------
        like:
          lang, disabled, readonly, required
    """

    name = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=2, max=140),
        ],
        render_kw={
            "class": "form-control",
            "autofocus": "true",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",
        },
    )

    visible = BooleanField(
        "",
        render_kw={"class": "form-check-input"},
    )

    color = StringField(
        "",
        validators=[Length(min=7, max=7)],
        default="#000000",
        id="id-color-inp",  # see .j2
        render_kw={
            "class": "form-control",
            "autocomplete": "off",
            "spellcheck": False,
            "placeholder": "#RRGGBB",
        },
        #  widget=ColorInput(),
    )

    title = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=2, max=140),
        ],  # TODO sidekick.config.DB_len_val_for_sep
        render_kw={
            "class": "form-control",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",
        },
    )

    description = StringField(
        "",
        validators=[Length(min=5, max=140)],
        render_kw={
            "class": "form-control",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",  # ⚠️ Don't define it here, they persist. See below ScmNew
        },
    )

    content = TextAreaField("", render_kw={"class": "form-control", "rows": "13"})


# Private form
class SpdEdit(FlaskForm):
    """
    ------------------------------------------------------------
       ⚠️
        Don't defined here mutable render_kw, they persist
        set value to those that will not change throw tha app
        see:
            carranca/private/sep_new_edit.py
                fform = SepNew(request.form) if is_new
                        else
                        SepEdit(request.form)
    ------------------------------------------------------------
        like:
          lang, disabled, readonly, required
    """

    name = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=2, max=140),
        ],
        render_kw={
            "class": "form-control",
            "autofocus": "true",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",
        },
    )

    # color = StringField(
    #     "",
    #     validators=[Length(min=7, max=7)],
    #     default="#000000",
    #     id="id-color-inp",  # see .j2
    #     render_kw={
    #         "class": "form-control",
    #         "autocomplete": "off",
    #         "spellcheck": False,
    #         "placeholder": "#RRGGBB",
    #     },
    #     #  widget=ColorInput(),
    # )

    title = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=2, max=140),
        ],  # TODO sidekick.config.DB_len_val_for_sep
        render_kw={
            "class": "form-control",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",
        },
    )

    description = StringField(
        "",
        validators=[Length(min=5, max=140)],
        render_kw={
            "class": "form-control",
            "autocomplete": "off",
            "spellcheck": True,
            "lang": "",  # ⚠️ Don't define it here, they persist.
        },
    )

    spd_file = FileField("", render_kw={"class": "form-control", "accept": ".gpkg"})

    field_attributes = {
        "class": "form-control",
        "autocomplete": "off",
        "list": "field_list",
    }

    # Spatial data attributes (fields)
    field_ID = StringField(
        "",
        validators=[Length(min=2, max=12)],
        render_kw=field_attributes,
    )

    field_name = StringField(
        "",
        validators=[Length(min=2, max=12)],
        render_kw=field_attributes,
    )

    field_alt_name = StringField(
        "",
        validators=[Length(min=2, max=12)],
        render_kw=field_attributes,
    )


# eof
