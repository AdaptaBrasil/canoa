"""
*Routes*
Private Routes
This routes are private, users _must be_ logged

Equipe da Canoa -- 2024
mgd
"""

# cSpell: ignore werkzeug wtforms tmpl mgmt jscmd


from __future__ import annotations

from flask import Blueprint, request
from typing import Tuple, Callable, cast
from datetime import datetime
from flask_login import login_required, current_user

from ..models.public import get_user_where
from ..helpers.py_helper import is_str_none_or_empty, to_str
from ..helpers.pw_helper import internal_logout, nobody_is_logged
from ..public.ups_handler import ups_handler
from ..helpers.uiact_helper import UiActResponse, UiActResponseProxy, UiActResponseKeys
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import (
    NEW_FLASK_RESPONSE,
    Jinja_Rendered,
    Flask_Response,
    Json_Text,
    Route_Response,
)
from ..helpers.js_consts_helper import js_form_cargo_id, js_form_sec_check
from ..helpers.route_helper import (
    get_private_response_data,
    base_route_private,
    private_route,
    is_method_post,
    is_method_get,
    login_route,
    redirect_to,
    get_method,
    bp_name,
    MTD_GET,
    MTD_POST,
    MTD_BOTH,
)

# === module variables ====================================
bp_private = Blueprint(bp_name(base_route_private), base_route_private, url_prefix="")
ROUTE_EMAIL_ADDR_HUB = "email_addr_hub"


# === Test _ route ========================================
@bp_private.route("/test_route")
def test_route():
    return "OK"


# === Private Routes =======================================
@bp_private.route("/home")
def home():
    """
    `home` page is the _landing page_
     for *users* (logged visitors).

    It displays the main menu.
    """

    if nobody_is_logged():
        return redirect_to(login_route())

    template, _, ui_db_texts = get_private_response_data("home")
    return process_template(template, **ui_db_texts.data())


@login_required
@bp_private.route("/sep_mgmt", methods=MTD_BOTH)
def sep_mgmt():
    """
    Through this route, the admin user can manage which
    user is the manager of a SEP

    """
    if nobody_is_logged():
        return redirect_to(login_route())
    else:
        from .sep_mgmt.sep_mgmt import sep_mgmt

        return sep_mgmt()


def create_ups_jHtml(error: str, code: int = 0) -> Jinja_Rendered:
    _, tmpl_ffn, ui_texts = ups_handler(code, error)
    jHtml = process_template(tmpl_ffn, **ui_texts)
    return jHtml


def uiact_response(
    code: str,
) -> Tuple[Jinja_Rendered, UiActResponse | None]:
    """
    This func decodes a uiact response
    """

    jHtml: Jinja_Rendered = ""
    uiact_rsp = None
    try:
        rqs_method = get_method()

        def _get_error(param: str) -> str:
            return f"Unexpected uiact route parameter [{param}]."

        def _get_result() -> Tuple[Jinja_Rendered, UiActResponse | None]:
            uiact_rsp = None
            jHtmlError: Jinja_Rendered = ""
            cmd_text: Json_Text = request.args.get(js_form_cargo_id, "") if rqs_method == MTD_GET else request.form.get(js_form_cargo_id, "")
            if is_str_none_or_empty(cmd_text):
                jHtmlError = create_ups_jHtml(_get_error("empty"))
            elif not (uiact_rsp := UiActResponse(cmd_text)):
                jHtmlError = create_ups_jHtml(_get_error("none"))
            elif is_str_none_or_empty(uiact_rsp.action):
                jHtmlError = create_ups_jHtml(_get_error("action: ''"))

            return jHtmlError, uiact_rsp

        if rqs_method == MTD_POST and not is_str_none_or_empty(msg_error_key := js_form_sec_check()):
            jHtml = create_ups_jHtml(msg_error_key)
        elif code == js_form_cargo_id:
            # the code is send via a html form's input or on the parameter
            jHtml, uiact_rsp = _get_result()
        elif not is_str_none_or_empty(code):
            uiact_rsp = UiActResponse(code)
        else:
            jHtml, uiact_rsp = _get_result()

    except Exception as e:
        uiact_rsp = None
        _, tmpl_ffn, ui_texts = ups_handler(0, str(e), e)
        jHtml = process_template(tmpl_ffn, **ui_texts)

    return jHtml, uiact_rsp


def grid_route(code: str, editor: str, show_grid: Callable[[], Jinja_Rendered]) -> Route_Response:
    """
    This func routes calls from a grid or to a grid. 8—|
    see sep_grid & scm_grid
    """

    if nobody_is_logged():
        return redirect_to(login_route())

    jHtmlOrResp: Route_Response = NEW_FLASK_RESPONSE
    jHtmlError, uiact_rsp = uiact_response(code)

    if jHtmlError:
        jHtmlOrResp = jHtmlError
    elif uiact_rsp and uiact_rsp.code == UiActResponseProxy.show:
        jHtmlOrResp = show_grid()
    elif uiact_rsp:

        def _goto(item_code: str) -> Flask_Response:
            url = private_route(editor, code=item_code)
            return redirect_to(url)

        match uiact_rsp.action:
            case UiActResponseKeys.insert:
                return _goto(UiActResponseProxy.add)
            case UiActResponseKeys.edit:
                data = uiact_rsp.encode()
                jHtmlOrResp = _goto(data)
            case UiActResponseKeys.delete:
                jHtmlOrResp = create_ups_jHtml("The `delete` procedure is under development.")
            case _:
                jHtmlOrResp = create_ups_jHtml(f"Unknown route action '{uiact_rsp.action}'.")

    return jHtmlOrResp


@login_required
@bp_private.route("/sep_grid/<code>", methods=MTD_BOTH)
def sep_grid(code: str = "?"):
    """
    Through this route, the admin user can CRUD seps and display a grid
    """

    from .sep_grid import get_sep_grid

    return grid_route(code, "sep_edit", get_sep_grid)


@login_required
@bp_private.route("/sep_edit/<code>", methods=MTD_BOTH)
def sep_edit(code: str = "?"):
    """
    Through this route, the user can edit a SEP
    """

    if nobody_is_logged():
        return redirect_to(login_route())

    from .sep_new_edit import do_sep_edit

    return do_sep_edit(code)


@login_required
@bp_private.route("/scm_export/<code>", methods=MTD_BOTH)
def scm_export(code: str = "?"):
    """
    Through this route, the user gets the export UI
    Where the SEP arrangement can be edited and/or DB exported
    """
    if nobody_is_logged():
        return redirect_to(login_route())

    jHtmlError, uiact_rsp = uiact_response(code)
    if not is_str_none_or_empty(jHtmlError) or uiact_rsp is None:
        # `uiact_rsp is None`` is for typing hints
        return jHtmlError

    elif uiact_rsp.code == UiActResponseProxy.show:
        from .scm_export_ui_show import scm_export_ui_show

        return scm_export_ui_show(uiact_rsp)
    elif uiact_rsp.action == UiActResponseKeys.export:
        from .scm_export_db import scm_export_db

        return scm_export_db(uiact_rsp)
    elif uiact_rsp.action == UiActResponseKeys.save:
        from .scm_export_ui_save import scm_export_ui_save

        return scm_export_ui_save(uiact_rsp)

    return redirect_to(login_route())


@login_required
@bp_private.route("/scm_grid/<code>", methods=MTD_BOTH)
def scm_grid(code: str = "?"):
    """
    Through this route, the user can edit and insert a Schema
    """
    from .scm_grid import get_scm_grid

    return grid_route(code, "scm_edit", get_scm_grid)


@login_required
@bp_private.route("/scm_edit/<code>", methods=MTD_BOTH)
def scm_edit(code: str = "?"):
    """
    Through this route, the user can edit a Schema
    """

    if nobody_is_logged():
        return redirect_to(login_route())
    else:
        from .scm_new_edit import do_scm_edit

        return do_scm_edit(code)


@login_required
@bp_private.route("/spd_edit/<code>", methods=MTD_BOTH)
def spd_edit(code: str = "?"):
    """
    Through this route, the admin user can CRUD spatial data and display a grid
    """

    if nobody_is_logged():
        return redirect_to(login_route())
    else:
        from .spd_new_edit import do_spd_edit

        return do_spd_edit(code)


@login_required
@bp_private.route("/receive_file", methods=MTD_BOTH)
def receive_file():
    """
    Through this route, the user sends a zip file or a URL link for validation.

    If it passes the simple validations confronted in receive_file.py,
    it is unzipped and sent to data_validate
    (see module `data_validate`).
    The report generated by `data_validate` is sent by e-mail and
    a result message is displayed to the user.

    Part of Canoa `Data Validation` Processes
    """

    if nobody_is_logged():
        return redirect_to(login_route())
    else:
        from .receive_file import receive_file

        tmpl = receive_file()
        return tmpl


@login_required
@bp_private.route("/received_files_mgmt", methods=MTD_BOTH)
def received_files_mgmt():
    """
    Through this route, the user gets a grid that allows
    him to manage and download the files he has sent for
    validation.

    When the user is power_user, he can request files from an other user_id
    """

    if nobody_is_logged():
        return redirect_to(login_route())
    elif is_method_get():
        return redirect_to(login_route())
    else:
        rid = request.args.get("id", type=int)  # Get 'id' from Request
        id = current_user.id if rid is None else rid
        from .received_files.init_grid import init_grid

        jHtml = init_grid(id)

        return jHtml


@login_required
@bp_private.route("/received_file_download", methods=[MTD_POST])
def received_file_download():
    """
    Through this route, the user request to download one of the files
    he has send for validation or it's generated report.
    """
    if nobody_is_logged():
        return redirect_to(login_route())
    else:
        from .received_files.download_record import download_rec

        rsp = download_rec()
        return rsp


@login_required
@bp_private.route("/log_me_out", methods=[MTD_GET, MTD_POST])
def log_me_out():
    """
    Finally the logout proc is a Canoa form (and not the js Confirm)
    he has send for validation or it's generated report.
    """
    if is_method_get() or nobody_is_logged():
        return redirect_to(login_route())
    else:
        from ..private.access_control.logout_user import log_me_out

        jHtml = log_me_out()
        return jHtml


@login_required
@bp_private.route(f"/{ROUTE_EMAIL_ADDR_HUB}", defaults={"uid": ""}, methods=MTD_BOTH)
@bp_private.route(f"/{ROUTE_EMAIL_ADDR_HUB}/<uid>", methods=MTD_BOTH)
def email_addr_hub(uid: str = "") -> Route_Response:
    """
    if user's email is verified:
        Sends a test email to the user's registered address to verify
        email deliverability and sending engine functionality.
    else:
        handles the registration email process

    """

    from ..models.public import User

    def __does_user_need_token(user_rec: User) -> bool:
        if is_str_none_or_empty(user_rec.verify_email_token):
            # Yes, user has no token
            return True

        from .access_control.email_addr_process import has_token_expired

        return has_token_expired(user_rec.verify_email_sent_at)

    jHtml: Jinja_Rendered = ""
    if nobody_is_logged():
        return redirect_to(login_route())

    elif not (user_rec := get_user_where(email=current_user.email)) or user_rec.disabled:
        # Maybe just deleted | disable?  | ?
        return redirect_to(login_route())

    elif user_rec.email_verified:
        # if user's email address was verified, send him a email
        from .access_control.email_addr_process import send_email_to_test_address

        jHtml = send_email_to_test_address(ROUTE_EMAIL_ADDR_HUB, current_user.email, current_user.username)

        return jHtml

    elif __does_user_need_token(user_rec):
        # user has no token or has expired
        from .access_control.email_addr_process import send_and_wait_verify_token, explain_email_addr_proc

        if uid:
            # The user accepted the process => send the verification email and wait for the input
            jHtml = send_and_wait_verify_token(current_user.email, current_user.username, uid)
        else:
            # Explain the user email address process, if accepted came bak with uid
            jHtml = explain_email_addr_proc(ROUTE_EMAIL_ADDR_HUB, current_user.email)

    else:
        # User has an active token to confirm, challenge the user ;-)
        from .access_control.email_addr_process import verify_sent_token

        db_token = to_str(user_rec.verify_email_token)
        email_sent_at = cast(datetime, user_rec.verify_email_sent_at)
        jHtml = verify_sent_token(current_user.email, db_token, email_sent_at)

    return jHtml


@login_required
@bp_private.route("/password_change", methods=MTD_BOTH)
def password_change():
    """
    'password_change page, as it's name
    implies, allows the user to change
    is password, for what ever reason
    at all or none.
    Whew! That's four lines :--)
    """

    if nobody_is_logged():
        return redirect_to(login_route())
    else:
        from .access_control.password_change import password_change

        return password_change()


@bp_private.route("/logout", methods=MTD_BOTH)
def logout() -> Flask_Response:
    """
    Logout the current user
    and the page is redirect to
    login
    """
    internal_logout()
    return redirect_to(login_route())


# eof
