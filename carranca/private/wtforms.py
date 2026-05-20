"""
*wtforms* HTML forms
Part of Private Access Control & `File Validation` Processes

Equipe da Canoa -- 2024
mgd 2024-04-09,27; 06-22, 2026-01
"""

# cSpell:ignore: wtforms urlname iconfilename tmpl RRGGBB gpkg attribs
import json
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

# ________________________________________________
# Typical StringField, 'render KeyWord arguments'
cls_render_kw = {"class": "form-control"}
str_render_kw = {
    **cls_render_kw,
    "autocomplete": "off",
    "spellcheck": True,
    "lang": "",  # ⚠️ Don't define it here, they persist.
}
select_render_kw = {"class": "form-select"}


# ________________________________________________
def apply_lang_to_string_fields(form: FlaskForm, value: str):
    """
    Sets render_kw['lang'] = value for every StringField in the form that has key 'lang'
    """
    _key = "lang"
    for _, field in form._fields.items():
        if isinstance(field, StringField) and field.render_kw and _key in field.render_kw:
            field.render_kw[_key] = value

    return


# ________________________________________________
# Empty Form
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
        render_kw=cls_render_kw,
    )


# Private form
class ReceiveFileForm(FlaskForm):
    schema_sep = SelectField("", validators=[DataRequired()], render_kw=select_render_kw)
    upload_file = FileField("", render_kw={**cls_render_kw, "accept": ".zip"})
    urlname = StringField("", validators=[URL()], render_kw=cls_render_kw)


# Private & Public form
class ChangePassword(FlaskForm):
    current_password = PasswordField(
        "",
        validators=[
            InputRequired(),
            Length(**sidekick.config.DB_len_val_for_pw.wtf_val()),
        ],
        render_kw=cls_render_kw,
    )

    password = PasswordField(
        "",
        validators=[
            InputRequired(),
            Length(**sidekick.config.DB_len_val_for_pw.wtf_val()),
        ],
        render_kw=cls_render_kw,
    )

    confirm_password = PasswordField(
        "",
        validators=[
            InputRequired(),
            Length(**sidekick.config.DB_len_val_for_pw.wtf_val()),
        ],
        render_kw=cls_render_kw,
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
        render_kw={**cls_render_kw, "disabled": True},  # almost
    )

    schema_name = StringField(
        "",
        validators=[Length(min=5, max=140)],  # TODO From DB
        render_kw={**cls_render_kw, "disabled": True},  # almost always disabled
    )

    sep_name = StringField(
        "",
        validators=[Length(min=5, max=140)],  # TODO From DB
        render_kw=str_render_kw,
    )

    description = StringField(
        "",
        validators=[InputRequired(), Length(min=5, max=140)],
        render_kw=str_render_kw,
    )

    icon_file = FileField("", render_kw={**cls_render_kw, "accept": ".svg"})

    # class is special for bootstrap (the only checkbox in Canoa): frm-check-for-bs
    visible = BooleanField("")


# Derived Private form
class SepNew(SepEdit):

    manager_list = SelectField(
        "",
        validators=[DataRequired()],
        coerce=int,
        render_kw=select_render_kw,
    )

    schema_list = SelectField(
        "",
        validators=[DataRequired()],
        coerce=int,
        render_kw=select_render_kw,
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
            **str_render_kw,
            "autofocus": "true",
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
            **str_render_kw,
            "spellcheck": False,
            "placeholder": "#RRGGBB",
        },  #  widget=ColorInput()
    )

    title = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=2, max=140),
        ],
        render_kw=str_render_kw,
    )

    description = StringField("", validators=[Length(min=5, max=140)], render_kw=str_render_kw)

    content = TextAreaField("", render_kw={**cls_render_kw, "rows": "13"})


# Private form
class SpdForm(FlaskForm):
    spd_name = StringField("", validators=[InputRequired(), Length(min=2, max=140)], render_kw={**str_render_kw, "autofocus": "true"})

    spd_title = StringField("", validators=[InputRequired(), Length(min=2, max=140)], render_kw=str_render_kw)  # TODO read form db

    spd_description = StringField("", validators=[Length(min=5, max=140)], render_kw=str_render_kw)


class SpdInsert(SpdForm):
    _len_val = [Length(min=2, max=8)]
    # field_attributes.list is accessed outside (see .\private\spd_new_edit.py:do_spd_edit)
    field_attributes = {**cls_render_kw, "autocomplete": "off", "list": "field_list"}

    field_id = StringField("", validators=[DataRequired(), *_len_val])
    field_name = StringField("", validators=_len_val)
    field_alt_name = StringField("", validators=_len_val)
    upload_file = FileField("", validators=[InputRequired()], render_kw={**cls_render_kw, "accept": ".gpkg"})

    def __init__(self, s_ins_ph: str = "[]", *args, **kwargs):
        super().__init__(*args, **kwargs)

        # first of this list MUST be `field_id`` see carranca\private\spd_new_edit.py:_register_file
        self.field_list = [self.field_id, self.field_name, self.field_alt_name]

        try:
            ins_ph = json.loads(s_ins_ph)  # always be cautious with ui_db_texts
        except:
            sidekick.display.error(f"Error decoding JSON place holders string [{s_ins_ph}].")
            ins_ph = []

        ins_ph = (ins_ph if isinstance(ins_ph, list) else []) + ([""] * len(self.field_list))
        for i, field in enumerate(self.field_list):
            field.render_kw = {**self.field_attributes, "placeholder": str(ins_ph[i])}
            field.data = str(ins_ph[i]) if ins_ph[i] else None


class SpdEdit(SpdForm):

    field_id = SelectField("", validators=[DataRequired()], choices=[], render_kw=select_render_kw)
    field_name = SelectField("", choices=[], render_kw=select_render_kw)
    field_alt_name = SelectField("", choices=[], render_kw=select_render_kw)
    original_file_name = StringField("", render_kw={**cls_render_kw, "readonly": True, "disabled": True})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # first of this list MUST be `field_id`` see carranca\private\spd_new_edit.py:_register_file
        self.field_list = [self.field_id, self.field_name, self.field_alt_name]


# eof
