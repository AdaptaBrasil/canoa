"""*app_context_vars*

Request Context
---------------
Contains the mechanisms to store and retrieve variables from Flask's g object.

The `g` object is a global namespace for holding any data you want during the
lifetime of a request.

It is unique to each request and is used to store and share data across different
parts of your application, such as between view functions, before/after
request functions, and other request handlers.


Application Context
-------------------
Contains a shortcut to the global sidekick object.


-- [/!\] -------
    Avoid calling any of these functions in `main.py` or `carranca.__init__.py`
    as there is no `has_request_context` and a sidekick is already running.



Equipe da Canoa -- 2025
mgd


"""

# cSpell:ignore mgmt

from flask import has_request_context, g
from typing import Callable, Any, Optional
from threading import Lock
from flask_login import current_user
from werkzeug.local import LocalProxy

from carranca import global_sidekick
from .Sidekick import Sidekick
from ..private.User_sep import UserSEP
from ..private.JinjaUser import JinjaUser
from ..private.LoggedUser import LoggedUser

# share global sidekick
sidekick: Sidekick = global_sidekick


# local lock control
_locks = {}


def _get_scoped_var(var_name: str, func_creator: Callable[[], Any]) -> Optional[Any]:
    """
    Returns a variable from the current request context, creating it if necessary.
    """

    if not has_request_context():  # no g
        return None
    elif var_name not in _locks:  # lock it, thread safety
        _locks[var_name] = Lock()

    with _locks[var_name]:
        if not hasattr(g, var_name):
            setattr(g, var_name, func_creator())

    return getattr(g, var_name, None)


# Logged User
# -----------
def _get_logged_user() -> Optional[LoggedUser]:
    from ..helpers.pw_helper import is_someone_logged

    """
    Info of the logged user or None if no one is logged
    """
    if is_someone_logged():
        return _get_scoped_var("_logged_user", LoggedUser)
    else:
        return None


# Logged User
# -----------
def _get_jinja_user() -> Optional[JinjaUser]:
    def _do_jinja_user() -> JinjaUser:
        return JinjaUser(_get_logged_user())

    jinja_user = _get_scoped_var("_jinja_user", _do_jinja_user)

    return jinja_user


# User SEP
# -----------
def do_user_sep() -> Optional[UserSEP]:
    from ..private.sep_icon import icon_prepare_for_html

    url, sep_fullname, sep = icon_prepare_for_html(current_user.mgmt_sep_id)
    user_sep = UserSEP(url, sep_fullname, sep)

    return user_sep


def _get_user_sep() -> Optional[UserSEP]:
    from ..helpers.pw_helper import is_someone_logged

    if is_someone_logged():
        return _get_scoped_var("_user_sep", do_user_sep)
    else:
        return None


# Proxies
# -------
logged_user: Optional[LoggedUser] = LocalProxy(_get_logged_user)


jinja_user: Optional[JinjaUser] = LocalProxy(_get_jinja_user)


user_sep: Optional[UserSEP] = LocalProxy(_get_user_sep)


# eof
