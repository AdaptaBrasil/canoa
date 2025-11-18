"""
*ups_handler*

    Handles exceptions and errors by displaying an HTML page.

Displays a html page to the user with
relevant information about the error.

    Ups Files
    ---------
    /public/ups_handler.py
    /static/icons/ups_handler.svg
    /templates/home/ups_page.html.j2

TODO
It logs the error and sends an e-mail to the admin.

Equipe da Canoa -- 2025
mgd 2025-03-05
"""

# cSpell:ignore

import html
import inspect
from typing import Tuple, Any

from ..common.UIDBTexts import UIDBTexts
from ..helpers.py_helper import is_str_none_or_empty
from ..helpers.pw_helper import internal_logout, is_someone_logged
from ..helpers.html_helper import icon_url
from ..helpers.types_helper import JinjaGeneratedHtml
from ..helpers.jinja_helper import process_template
from ..helpers.route_helper import get_tmpl_full_file_name
from ..config.local_ui_texts import AuxTexts, local_ui_texts, local_form_texts
from ..common.app_error_assistant import AppStumbled
from ..helpers.ui_db_texts_helper import DBTexts, UITextsKeys, add_msg_final, get_section


def get_ups_jHtml(
    ui_item_error_key: str, ui_db_texts: UIDBTexts, task_code: int, e: Exception | None = None, *args
) -> JinjaGeneratedHtml:
    msg = add_msg_final(ui_item_error_key, ui_db_texts, *args)
    _, tmpl_rfn, ui_texts = ups_handler(task_code, msg, e)
    jHTML = process_template(tmpl_rfn, **ui_texts)
    return jHTML


def ups_handler(
    error_code: int, user_msg: str, e: Exception | None = None, logout: bool = False
) -> Tuple[dict, str, DBTexts]:
    from ..common.app_context_vars import app_user, sidekick

    try:
        ui_texts = get_section(f"Ups-{error_code}")
    except:
        ui_texts = local_ui_texts(UITextsKeys.Fatal.no_db_conn)

    def _get_tech_msg():
        tech_msg = getattr(e, "tech_info", "")
        return (
            tech_msg if tech_msg else local_ui_texts(AuxTexts.section)[AuxTexts.techIntro].format(sidekick.log_filename)
        )

    tech_msg = ""
    error_msg = ""
    if not e:
        error_msg = ""  # no error, just a message for the user
    elif isinstance(e, AppStumbled):
        error_code = e.error_code
        error_msg = e.msg
        logout = e.logout
        tech_msg = _get_tech_msg()
    elif app_user.is_power if app_user else False:
        error_msg = html.escape(str(e))
        tech_msg = _get_tech_msg()
    else:  # common user with error: display user_msg & log_filename
        tech_msg = _get_tech_msg()

    # Get the name of the caller function
    caller_function = inspect.stack()[1].function

    # default texts that can be use in the form (see ups_page)
    context_texts = {
        UITextsKeys.Msg.tech: tech_msg,
        UITextsKeys.Msg.warn: user_msg,
        UITextsKeys.Msg.error: error_msg,
        UITextsKeys.Msg.display_only_msg: True,
        UITextsKeys.Fatal.code: error_code,
        UITextsKeys.Fatal.where: caller_function,
        UITextsKeys.Fatal.http_code: 500,
    }

    def _should_update(key: str, value: Any) -> bool:
        return not is_str_none_or_empty(value) and (key not in ui_texts or is_str_none_or_empty(ui_texts.get(key)))

    # Add `context_texts` if the key is missing from ui_texts or its value is empty.
    for key, value in context_texts.items():
        if _should_update(key, value):
            ui_texts[key] = value

    # Add `local_form_texts` if the key is missing or its value is empty.
    for key, value in local_form_texts().items():
        if _should_update(key, value):
            ui_texts[key] = value

    # set the url for the icon IF a file name exists
    if (file_name := ui_texts.get(UITextsKeys.Form.icon_file)) and not ui_texts.get(UITextsKeys.Form.icon_url):
        ui_texts[UITextsKeys.Form.icon_url] = icon_url("icons", file_name)

    # before logout
    sidekick.app_log.error(e)
    sidekick.app_log.debug(error_msg)

    # TODO: send email
    if logout and is_someone_logged():
        internal_logout()

    ups_tmpl_file_name = get_tmpl_full_file_name("ups_page", "home")

    return {}, ups_tmpl_file_name, ui_texts


# eof
