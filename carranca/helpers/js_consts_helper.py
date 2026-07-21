"""
Grid HTML + js + py communication constants

Equipe da Canoa -- 2025
mgd 2025-01-19 -- 10-08
"""

# TODO: ui_form_helper


# cSpell:ignore

import json
from flask import request
from typing import List, Final, Dict
from flask_login import current_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from .types_helper import JS_Constants

from ..helpers.py_helper import to_str
from ..common.app_error_assistant import AppStumbled

# === Global js constants Keys for JsConstants Jinja Dictionary for j2 grid/form/security ====
#
#  Key name const
#  --------------
#  Uses Python variable style names and starts with 'js_const_'
#
#  js_ui_dict Key name
#  -------------------
#  Uses Python variable style names and starts with 'grid_'
#
#  uiTexts Key name
#  ----------------
#  Uses PascalCase style names (see ui_items Database View)


JS_FORM_SEC_KEY: Final[str] = "form_sec_key"
JS_FORM_CARGO_ID: Final[str] = "form_cargo_id"  # don't use  "form-cargo-id" (raise errors & errors)


# Signed, time-limited form token: proves a POST's hidden `form_sec_key` field came from
# a page Canoa itself rendered for this same user, recently -- not a real secret hidden
# from the browser (it round-trips through a hidden input), just tamper-evidence, so
# signing (itsdangerous) is enough; no need for actual encryption.
_SEC_TOKEN_SALT: Final[str] = "canoa-form-sec-token"
_SEC_TOKEN_MAX_AGE_SECONDS: Final[int] = 4 * 3600  # generous: don't punish a user who left a grid open

_ANONYMOUS_ID: Final[int] = -5612

_SEC_TOKEN_KEY_USER: Final[str] = "u"
_SEC_TOKEN_KEY_MSG: Final[str] = "m"


def _sec_token_serializer() -> URLSafeTimedSerializer:
    from ..common.app_context_vars import sidekick

    return URLSafeTimedSerializer(sidekick.config.SECRET_KEY, salt=_SEC_TOKEN_SALT)


def _sec_token_user_id() -> int:
    return current_user.id if current_user and current_user.is_authenticated else _ANONYMOUS_ID


def js_form_sec_value(msg: str = "") -> str:
    return _sec_token_serializer().dumps({_SEC_TOKEN_KEY_USER: _sec_token_user_id(), _SEC_TOKEN_KEY_MSG: msg})


# }

# Grid
JS_GRID_COL_META_INFO: Final[str] = "colMetaInfo"

# ui_texts security key msg error key (in DB ui_items)
UI_TEXTS_SEC_ERROR_KEY: Final[str] = "secKeyViolation"


def _js_form_sec_load(expect_authenticated: bool) -> Dict:
    value = request.form.get(JS_FORM_SEC_KEY, "")

    try:
        data = _sec_token_serializer().loads(value, max_age=_SEC_TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return {}

    is_valid = data.get(_SEC_TOKEN_KEY_USER) == (_sec_token_user_id() if expect_authenticated else _ANONYMOUS_ID)
    return data if is_valid else {}


def js_form_sec_check(expect_authenticated: bool = True) -> str:

    data = _js_form_sec_load(expect_authenticated)
    return "" if data else UI_TEXTS_SEC_ERROR_KEY


def js_form_get_sec_msg() -> str:
    data = _js_form_sec_load(True)
    return to_str(data.get(_SEC_TOKEN_KEY_MSG)) if data else ""


def js_ui_dictionary(col_meta_info_txt: str = "", col_names: List[str] = [], task_code: int = 1) -> JS_Constants:
    """
    col_meta_info_txt -> json text from table 'ui_items' key= [section]'colMetaInfo'
       eg-> {"id":"", "name":"Nome", "color":"Cor", "visible":"Visível", "sep_v2t":"SEPs (visível/total)" }
    col_names -> list of column names that must be present in col_meta_info_txt

    """

    js_ui_dict: JS_Constants = {}

    js_ui_dict["grid_id"] = "ag-grid-id"
    js_ui_dict[JS_FORM_CARGO_ID] = JS_FORM_CARGO_ID

    """ little bit of 'recursive':
        can be used as `js_ui_dict.form_sec_key` or, in macros, `just `form_sec_key`
    """
    js_ui_dict["js_ui_dict"]: JS_Constants = js_ui_dict  # type: ignore

    if col_meta_info_txt:
        col_meta_info_json = json.loads(col_meta_info_txt)
        # TODO: hide => v=  header == '', flex => f = 1 or from db
        col_meta_info_array = [{"n": key, "h": col_meta_info_json[key]} for key in col_meta_info_json]
        col_meta_info_names = {item["n"] for item in col_meta_info_array}

        if col_meta_info_names and not set(col_names).issubset(col_meta_info_names):
            missing_keys = set(col_names) - col_meta_info_names
            # this is a error for the developer
            raise AppStumbled(
                f"Invalid MetaInfo columns mapping: `{col_meta_info_txt}` &ne; [{', '.join(col_names)}]. Missing keys: {missing_keys}",
                task_code,
            )

        # short for 'n': name, 'h': header
        js_ui_dict["grid_col_meta"] = [{"n": key, "h": col_meta_info_json[key]} for key in col_meta_info_json]  # type: ignore

    return js_ui_dict


# eof
