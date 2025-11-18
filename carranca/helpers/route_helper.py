"""
Python functions to assist routes.py

mgd 2024-05-13
Equipe da Canoa -- 2024
"""

# cSpell:ignore werkzeug tmpl

import requests
from os import path
from flask import redirect, request, url_for
from typing import Tuple, Optional

from .py_helper import is_str_none_or_empty, camel_to_snake, clean_text
from .html_helper import URL_PATH_SEP
# 2/3. This line produce the sidekick-incident
from .jinja_helper import TemplateFileFullName
from .types_helper import JinjaGeneratedHtml
from ..common.UIDBTexts import UIDBTexts
from .ui_db_texts_helper import get_db_texts

from ..config import BaseConfig

ResponseData = Tuple[JinjaGeneratedHtml, bool, UIDBTexts]

base_route_private = "private"
base_route_public = "public"
base_route_static = "static"
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


def get_form_input_value(name: str, not_allowed: Optional[str] = "") -> str:
    text = request.form.get(name)
    return "" if text is None else clean_text(text, not_allowed)


def get_tmpl_full_file_name(tmpl: str, folder: str) -> TemplateFileFullName:
    from ..common.app_context_vars import sidekick

    tmpl_file_name = f"{tmpl}.html.j2"
    # template *must* be with '/':
    tmpl_full_file_name: TemplateFileFullName = f".{URL_PATH_SEP}{folder}{URL_PATH_SEP}{tmpl_file_name}"
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

    tmpl_full_file_name, is_get, ui_db_texts = init_response_vars()
    try:
        tmpl_file_name = tmpl_file_name if tmpl_file_name else camel_to_snake(ui_db_section)
        tmpl_full_file_name = get_tmpl_full_file_name(tmpl_file_name, folder)

        db_texts = get_db_texts(ui_db_section)
        ui_db_texts = UIDBTexts(db_texts, sidekick.debugging)

    except Exception as e:
        # Re-raise exception to allow it to propagate
        sidekick.app_log.error(f"Failed in _get_response_data for section '{ui_db_section}': {e}")
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

    return _get_response_data(ui_texts_section, tmpl_base_name, "accounts")


def init_response_vars() -> ResponseData:
    """
    returns JinjaTemplate, is_get, ui_db_texts
    """
    is_get = is_method_get()
    return "", is_get, UIDBTexts({}, False)


def redirect_to(route: str, message: Optional[str] = None) -> str:
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
