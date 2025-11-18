"""
*Routes*
Part of Public Access Control Processes
This routes are public, users _must_ not be logged
(they will be redirect or raise an error, unauthorized_handler)

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore errorhandler

from flask import Blueprint, render_template

# from flask_login import LoginManager
from carranca import global_login_manager
from ..helpers.pw_helper import internal_logout, is_someone_logged
from ..helpers.route_helper import (
    MTD_BOTH,
    bp_name,
    home_route,
    redirect_to,
    index_route,
    login_route,
    is_method_get,
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
    return redirect_to(home_route() if is_someone_logged() else index_route())


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
    if is_someone_logged():
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
    if is_method_get() and is_someone_logged():
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
    if is_someone_logged():
        internal_logout()
        return unauthorized_handler()
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

    if is_someone_logged():
        return redirect_to(private_route("change_password"))
    else:
        from .access_control.password_recovery import password_recovery

        return password_recovery()


# new comers: <name> is a dynamic name
@bp_public.route("/docs/<publicDocName>")
def docs(publicDocName: str):
    from .display_html import display_html

    # TODO privateDocs for About
    return display_html(publicDocName)


# Common Errors -------------------------------------------
# 403 Forbidden
@bp_public.errorhandler(403)
def access_forbidden(error):
    return render_template("home/page-403.html"), 403


# 404 Not Found
@bp_public.errorhandler(404)
def not_found_error(error):
    return render_template("home/page-404.html"), 404


# 500 Internal Server Error
@bp_public.errorhandler(500)
def internal_error(error):
    return render_template("home/page-500.html"), 500


# Unauthorized Access -------------------------------------
@global_login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("home/page-403.html"), 403


# eof
