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


-- [⚠️] -------
    Avoid calling any of these functions in `main.py` or `carranca.__init__.py`
    as there is no `has_request_context` and a sidekick is already running.



Equipe da Canoa -- 2025
mgd

"""

# cSpell:ignore mgmt sepsusr usrlist
import sys
from flask import has_request_context, g
from typing import TYPE_CHECKING, Callable, Optional, List, cast, Any
from flask_login import current_user
from werkzeug.local import LocalProxy

# from ..private.AppUser import AppUser
# went to TYPE_CHECKING & Inside _get_app_user
# from ..private.JinjaUser import JinjaUser

if TYPE_CHECKING:
    from ..private.UserSep import UserSepList, UserSepsRtn
    from ..private.AppUser import AppUser
    from ..private.JinjaUser import JinjaUser


def local_sidekick():
    # Retrieve the module itself from sys.modules
    # Then access the 'sidekick' attribute, which triggers your __getattr__
    return sys.modules[__name__].sidekick


def __get_scoped_var(var_name: str, do_var_creator: Callable[[], Any]) -> Any:
    """
    Returns a value from the current request context (g), creating it if necessary.
    """
    if not has_request_context():
        raise RuntimeError(f"Request context is required to retrieve `{var_name}`.")

    if not hasattr(g, var_name):
        try:
            var_value = do_var_creator()
            if var_value is None:
                raise ValueError(f"{do_var_creator} returned None for `{var_name}`.")
            setattr(g, var_name, var_value)
            local_sidekick().display.info(f"{var_name} created, type: {type(var_value)}")
        except Exception as e:
            raise RuntimeError(f"Scoped variable creator {do_var_creator} raised an exception [{e}].")
        return var_value
    else:
        return getattr(g, var_name)


# App User
# -----------
def __get_app_user() -> Optional["AppUser"]:
    from ..helpers.pw_helper import is_anyone_logged
    from ..private.AppUser import AppUser

    """
    Info of the logged user or None if no one is logged
    """
    if is_anyone_logged():
        return __get_scoped_var("_app_user", AppUser)
    else:
        return None


# Jinja User (few attributes, as this user is exposed to HTML files via Jinja)
# --------------
def __get_jinja_user() -> Optional["JinjaUser"]:
    def _do_jinja_user() -> Optional["JinjaUser"]:
        from ..private.JinjaUser import JinjaUser

        result = __get_app_user()
        return JinjaUser(result) if result else None

    jinja_user = __get_scoped_var("_jinja_user", _do_jinja_user)

    return jinja_user


# User SEPs
# -----------
# IMPROVEMENT: make this an ajax call
def __prepare_user_seps() -> "UserSepsRtn":

    from ..private.UserSep import UserSep
    from ..private.sep_icon import do_icon_get_url
    from ..helpers.pw_helper import is_anyone_logged
    from ..models.private.mgmt_seps_user import MgmtSepsUser

    user_id: int = current_user.id if is_anyone_logged() else -1

    try:
        sep_usr_rows = MgmtSepsUser.get_user_sep_list(user_id)
    except Exception as e:
        return str(e)

    seps: List[UserSep] = []
    for sep_row in sep_usr_rows:
        item = UserSep(**sep_row)
        item.icon_url = do_icon_get_url(item.icon_file_name, item.id)
        seps.append(item)

    local_sidekick().display.debug(f"user_seps created: {len(seps)} item(s).")
    return seps


def __get_user_seps() -> "UserSepList":
    result = []
    if not app_user:
        local_sidekick().display.error("No current user to retrieve SEP data.")
    else:
        seps = __get_scoped_var("_user_seps", __prepare_user_seps)
        if seps is None or not isinstance(seps, list):
            local_sidekick().display.error(f"Error getting seps for user {app_user.id}: [{type(seps)}] → {str(seps)}.")
        else:
            result = seps

    return result


# =========================================================
# Proxies
# =========================================================

app_user: "AppUser" = cast("AppUser", LocalProxy(__get_app_user))
user_seps: "UserSepsRtn" = cast("UserSepsRtn", LocalProxy(__get_user_seps))
jinja_user: Optional["JinjaUser"] = cast(Optional["JinjaUser"], LocalProxy(__get_jinja_user))


def __getattr__(name):
    """Dynamically resolves 'sidekick' to retrieve the current value of global_sidekick."""
    if name == "sidekick":
        from carranca import global_sidekick

        if global_sidekick is None:
            raise RuntimeError(
                "🚨 Application accessed before initialization. global_sidekick is None. " "Check import order or application setup."
            )
        return global_sidekick

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Keep __setattr__ to enforce read-only status
def __setattr__(name, value):
    if name == "sidekick":
        raise AttributeError(f"Cannot assign to attribute '{name}' of module '{__name__}'. It is read-only.")
    globals()[name] = value
