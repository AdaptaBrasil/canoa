"""
Grid HTML + js + py communication constants

Equipe da Canoa -- 2025
mgd 2025-01-19 -- 10-08
"""

# TODO: ui_form_helper


# cSpell:ignore

import json
from flask import request
from typing import Optional, List

from ..common.app_error_assistant import AppStumbled
from .types_helper import JsConstants


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

# ------------------------
# see carranca\__init__.py
# safe_token= {"key": js_form_sec_key, "value": js_form_sec_value(), "cargo": js_form_cargo_id }
js_form_sec_key = "form_sec_key"
js_form_cargo_id = "form_cargo_id"  # don't use  "form-cargo-id" (raise errors & errors)


def js_form_sec_value() -> str:
    # TODO: create a real key with user_id and datetime
    return "7298kaj0fk9dl-sd=)0ya16"


# }

# Grid
js_grid_col_meta_info = "colMetaInfo"

# ui_texts secury ley msg error key (in DB ui_items)
ui_texts_sec_error_key = "secKeyViolation"


def js_form_sec_check(value: Optional[str] = None) -> str:
    # TODO "secKey"
    check = value if value else request.form.get(js_form_sec_key, "")

    msg_error = "" if check == js_form_sec_value() else ui_texts_sec_error_key
    # "secKeyExpired"
    # ...'TODO
    return msg_error


def js_ui_dictionary(col_meta_info_txt: str = "", col_names: List[str] = [], task_code: int = 1) -> JsConstants:

    js_ui_dict: JsConstants = {}

    js_ui_dict["grid_id"] = "ag-grid-id"
    js_ui_dict[js_form_cargo_id] = js_form_cargo_id

    # # TODO see _ini_py:_register_jinja
    # js_ui_dict[js_form_sec_key] = js_form_sec_key  # security token key
    # js_ui_dict["form_sec_value"] = js_form_sec_value()  # security token value

    """ little bit of 'recursive':
        can be used as `js_ui_dict.form_sec_key` or, in macros, `just `form_sec_key`
    """
    js_ui_dict["js_ui_dict"]: JsConstants = js_ui_dict  # type: ignore

    if col_meta_info_txt:
        col_meta_info_json = json.loads(col_meta_info_txt)
        # TODO: hide => v=  header == '', flex => f = 1 or from db
        col_meta_info_array = [{"n": key, "h": col_meta_info_json[key]} for key in col_meta_info_json]
        col_meta_info_names = {item["n"] for item in col_meta_info_array}

        if col_meta_info_names and not set(col_names).issubset(col_meta_info_names):
            missing_keys = set(col_names) - col_meta_info_names
            # this is a error for the developer
            raise AppStumbled(
                f"Invalid MetaInfo columns mapping: `{col_meta_info_txt}` <> [{', '.join(col_names)}]. Missing keys: {missing_keys}",
                task_code,
            )

        # short for 'n': name, 'h': header
        js_ui_dict["grid_col_meta"] = [{"n": key, "h": col_meta_info_json[key]} for key in col_meta_info_json]  # type: ignore

    return js_ui_dict


# eof
