"""
Python functions to assist routes.py

mgd 2024-05-13
Equipe da Canoa -- 2024
"""

# cSpell:ignore werkzeug

import requests
from os import path
from flask import redirect, request, url_for
from typing import Tuple, Optional


from .py_helper import is_str_none_or_empty, camel_to_snake, clean_text
from .html_helper import URL_PATH_SEP

# 2/3. This line produce the sidekick-incident
from .html_helper import icon_url
from .jinja_helper import Template_File_Full_Name
from .types_helper import Jinja_Rendered, Flask_Response
from ..common.UIDBTexts import UIDBTexts
from ..config.BaseConfig import BaseConfig
from ..common.UITextsKeys import UITextsKeys
from .ui_db_texts_manager import init_ui_db_texts
from ..common.app_error_assistant import ModuleErrorCode

ResponseData = Tuple[Jinja_Rendered, bool, UIDBTexts]

base_route_private = "private"
base_route_public = "public"
base_route_static = "static"
base_route_account = "accounts"

public_route__password_reset = "password_reset"
templates_found = []

MTD_GET = "GET"
MTD_POST = "POST"
MTD_BOTH = [MTD_GET, MTD_POST]

MTD_UNEXPECTED_ERROR = "Unexpected Request Method. The procedure cannot be executed."

"""
  ## Dynamic Route:
  @bp_public.route("/docs/<publicDocName>")
  can handle multiple URLs by capturing the part after /docs/ as a parameter.

  ## Static Route:
  bp_public = Blueprint('bp_public', __name__, url_prefix='/docs')
  @bp_public.route('/privacyPolicy') handles a specific URL /docs/privacyPolicy.

"""


def _route(base: str, page: str, **params) -> str:
    try:
        address = f"{bp_name(base)}.{page}"
        url = url_for(address, **params)
    except:
        raise Exception(f"An error occurred while constructing the following address: [{base}.{page}/{params}]")
    return url


def bp_name(base: str) -> str:
    return f"bp_{base}"


def private_route(page: str, **params) -> str:
    return _route(base_route_private, page, **params)


def public_route(page: str, **params) -> str:
    return _route(base_route_public, page, **params)


def static_route(filename: str) -> str:
    return url_for(base_route_static, filename=filename)


def login_route() -> str:
    return public_route("login")


def register_route() -> str:
    """
    The `register` page can convert,
    a visitor into a user.
    Anyone can be (requested)
    """
    return public_route("register")


def index_route() -> str:
    return public_route("index")


def home_route() -> str:
    return private_route("home")


def get_method() -> str:
    return request.method.upper()


def is_method_get() -> bool:
    return not is_method_post()


def is_method_post() -> bool:
    """
    Determine if the current request method is GET.
    Raises a ValueError for unexpected request methods.
    """
    rm = get_method()
    is_get = rm == MTD_GET
    if is_get:
        pass
    elif rm == MTD_POST:
        is_get = False
    else:
        raise ValueError(f"Unexpected request method: '{rm}'.")

    return is_get


def get_form_input_value(name: str, not_allowed: str = "") -> str:
    text = request.form.get(name)
    return "" if text is None else clean_text(text, not_allowed)


def get_tmpl_full_file_name(tmpl: str, folder: str) -> Template_File_Full_Name:
    from ..common.app_context_vars import sidekick

    tmpl_file_name = f"{tmpl}.html.j2"
    # template *must* be with '/':
    tmpl_full_file_name: Template_File_Full_Name = f".{URL_PATH_SEP}{folder}{URL_PATH_SEP}{tmpl_file_name}"
    tmpl_full_name = path.join(".", sidekick.config.TEMPLATES_FOLDER, folder, tmpl_file_name)
    if tmpl_full_name in templates_found:
        pass
    elif path.isfile(tmpl_full_name):
        templates_found.append(tmpl_full_name)
    else:
        raise FileNotFoundError(f"The requested template '{tmpl_full_name}' was not found.")

    return tmpl_full_file_name


def _get_response_data(ui_db_section: str, tmpl_file_name: str, folder: str) -> ResponseData:
    from ..common.app_context_vars import sidekick

    tmpl_full_file_name, is_get, ui_db_texts, _ = init_response_vars(ModuleErrorCode.LEGACY_STYLE)
    try:
        tmpl_file_name = tmpl_file_name if tmpl_file_name else camel_to_snake(ui_db_section)
        tmpl_full_file_name = get_tmpl_full_file_name(tmpl_file_name, folder)
        # 2026.04.02
        # db_texts = get_db_texts(ui_db_section)
        # ## add to ui_db_texts useful values  of 'general use'
        # ui_dt_format = sidekick.config.APP_UI_DATETIME_FORMAT
        # db_lookup = cast(DB_Lookup, db_retrieve_text)
        # ui_db_texts = UIDBTexts(db_texts, sidekick.debugging, ui_dt_format, db_lookup)
        ui_db_texts = init_ui_db_texts(ui_db_section)
        # mgd 2026.05
        if icon_fn := ui_db_texts.get_str(UITextsKeys.Form.icon_file):
            ui_db_texts[UITextsKeys.Form.icon_url] = icon_url(icon_fn)

    except Exception as e:
        # Re-raise exception to allow it to propagate
        sidekick.display.error(f"Failed in _get_response_data for section '{ui_db_section}': {e}")
        raise

    return tmpl_full_file_name, is_get, ui_db_texts


def get_private_response_data(ui_texts_section: str, tmpl_base_name: str = "") -> ResponseData:
    """
    if tmpl_base_name is none is created based on ui_texts_section name
    eg:  receivedFilesMgmt -> received_files_mgmt.html.j2

    returns:
        - TemplateFileFullName, assumes that is in the `private` folder
        - is_get true when the request method is GET, false when is POST
        - UIDBTexts the DB ui texts for this Form/Grid etc.
    """
    return _get_response_data(ui_texts_section, tmpl_base_name, base_route_private)


def get_account_response_data(ui_texts_section: str, tmpl_base_name: str = "") -> ResponseData:
    """
    if tmpl_base_name is none is created based on ui_texts_section name
    eg:  receivedFilesMgmt -> received_files_mgmt.html.j2

    returns:
        - TemplateFileFullName, assumes that is in the `accounts` folder
        - is_get true when the request method is GET, false when is POST
        - UIDBTexts the DB ui texts for this Form/Grid etc.
    """

    return _get_response_data(ui_texts_section, tmpl_base_name, base_route_account)


def init_response_vars(error_code: ModuleErrorCode) -> Tuple[*ResponseData, int]:
    """
    returns JinjaTemplate, is_get, ui_db_texts
    """
    from ..common.app_context_vars import sidekick

    ui_dt_format = sidekick.config.APP_UI_DATETIME_FORMAT
    is_get = is_method_post()
    return "", is_get, UIDBTexts({}, False, ui_dt_format, None), (error_code.value if error_code else 1)


def redirect_to(route: str, message: Optional[str] = None) -> Flask_Response:
    # TODO: display message 'redirecting to ...
    return redirect(route)


def is_external_ip_ready(config: BaseConfig) -> bool:

    if is_str_none_or_empty(config.SERVER_EXTERNAL_IP):
        try:
            config.SERVER_EXTERNAL_IP = requests.get(config.EXTERNAL_IP_SERVICE).text.strip()
        except:
            # TODO: LOG
            config.SERVER_EXTERNAL_IP = ""

    return not is_str_none_or_empty(config.SERVER_EXTERNAL_IP)


# eof
