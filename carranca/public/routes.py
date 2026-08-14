"""
*Routes*
Part of Public Access Control Processes
This routes are public, users _must_ not be logged
(they will be redirect or raise an error, unauthorized_handler)

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore errorhandler
from http import HTTPStatus
from flask import Blueprint, render_template

from ..helpers.pw_helper import internal_logout, is_anyone_logged
from ..common.app_constants import PUBLIC_DOC_NAMES
from ..helpers.route_helper import (
    MTD_BOTH,
    bp_name,
    home_route,
    redirect_to,
    index_route,
    login_route,
    is_method_post,
    private_route,
    base_route_public,
    public_route__password_reset,
)

# === module variables ====================================
bp_public = Blueprint(bp_name(base_route_public), base_route_public, url_prefix="")


# === routes =============================================
@bp_public.route("/")
def route_default():
    """
    `default` page redirects a visitor
        according to it's status:
            if logged -> to `home`
            else -> to `index`.
    """
    return redirect_to(home_route() if is_anyone_logged() else index_route())


@bp_public.route("/index")
def index():
    """
    `index` page is the _landing page_
    for *visitors* (any person with access
    to the page, public).

    For now, it only redirects to the login,
    in the near future, it can be explained here
    about the site.
    """
    return redirect_to(login_route())


@bp_public.route("/register", methods=MTD_BOTH)
def register():
    """
    The `register` page can convert
    a visitor into a user,
    if he fills in a form correctly.
    """
    if is_anyone_logged():
        return redirect_to(login_route())
    else:
        from .access_control.register import register as do_register

        return do_register()


@bp_public.route("/login", methods=MTD_BOTH)
def login():
    """
    The `login` page can be access by everyone,
    it is *public*.

    It display a Login form that serves
    as a Menu, that gives access to
      [forget-password],
      [register] and
      the usual documents.
    """
    if is_method_post() and is_anyone_logged():
        return redirect_to(home_route())
    else:
        from .access_control.login import do_login

        return do_login()


@bp_public.route(f"/{public_route__password_reset}/<token>", methods=MTD_BOTH)
def password_reset(token=None):
    """
    Password Reset Form:
    When a user forgets their password, they will receive an
    email containing a link to a form where they can enter
    and confirm their new password.
    mgd 2024.03.21
    """
    if is_anyone_logged():
        from ..common.UITextsKeys import UITextsKeys
        from ..config.FormIcons import FormIcons as fi
        from ..helpers.ui_db_texts_manager import init_ui_db_texts

        internal_logout()
        code = HTTPStatus.UNAUTHORIZED
        ui_db_texts = init_ui_db_texts(UITextsKeys.Section.error)
        _, message = ui_db_texts.set_msg_fatal(f"HTTP-{code.value}")
        # one shared word (DB item "httpErrorTitle", eg. "Erro") reused as the title for every code
        title = f"{ui_db_texts.get_str('httpErrorTitle', 'Error')} {code}"
        ui_texts = {
            **ui_db_texts.data(),  # includes msgOnly=True, set by set_msg_fatal above
            UITextsKeys.Page.title: title,
            UITextsKeys.Form.title: title,
            UITextsKeys.Msg.error: message,
        }
        return render_template("home/html_error_page.html.j2", code=code, fi=fi.with_icon("http_error"), **ui_texts), code
    else:
        from .access_control.password_reset import password_reset

        return password_reset(token)


@bp_public.route("/password_recovery", methods=MTD_BOTH)
def password_recovery():
    """ "
    *Password Recovery Form*
    This form asks the user for his registered e-mail address
    so that a link with a token can be sent to him. This link
    would open a form to reset his password.
    *The user should not be authenticated*
    """

    if is_anyone_logged():
        return redirect_to(private_route("password_change"))
    else:
        from .access_control.password_recovery import password_recovery

        return password_recovery()


@bp_public.route("/docs/<publicDocName>")
def docs(publicDocName: str):
    """
    Displays a document (eg. `aboutApp`, `privacyPolicy`, `termsOfUse`).
    Despite living in `bp_public`, this route is only *partially* public:
    names in `PUBLIC_DOC_NAMES` are open to everyone (linked from login/
    register, before the user is authenticated); any other name requires
    an active session.
    """
    from .display_html import display_html

    if publicDocName.lower() not in PUBLIC_DOC_NAMES and not is_anyone_logged():
        return redirect_to(login_route())

    return display_html(publicDocName)


# eof
