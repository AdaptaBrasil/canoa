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
from typing import TYPE_CHECKING, Callable, Optional, Any, List
from flask_login import current_user
from werkzeug.local import LocalProxy


# from ..private.AppUser import AppUser
# went to TYPE_CHECKING & Inside _get_app_user
# from ..private.JinjaUser import JinjaUser

# local lock control
from threading import Lock

if TYPE_CHECKING:
    from ..private.UserSep import UserSepList, UserSepDict, UserSepsRtn
    from ..private.AppUser import AppUser
    from ..private.JinjaUser import JinjaUser


_locks = {}
_locks_lock = Lock()
RUN_WITH_LOCKS = True  # debug _get_scoped_var


def local_sidekick():
    # Retrieve the module itself from sys.modules
    # Then access the 'sidekick' attribute, which triggers your __getattr__
    return sys.modules[__name__].sidekick


def __get_scoped_var(var_name: str, do_var_creator: Callable[[], Any]) -> Any:
    """
    Returns a value, from the current request context (g) under the var_name , creating it if necessary.
    """

    if not has_request_context():  # no g
        raise RuntimeError(f"Request context is required to retrieve `{var_name}`.")

    _CREATION_FAILED = object()

    var_value = None
    if RUN_WITH_LOCKS:
        with _locks_lock:
            if var_name not in _locks:
                _locks[var_name] = Lock()

        with _locks[var_name]:
            if hasattr(g, var_name):
                var_value = getattr(g, var_name)
                print(f"{var_name} data found, using sema.")
                if var_value is _CREATION_FAILED:
                    raise RuntimeError(f"Previous attempt to create `{var_name}` failed.")
                return var_value
            else:
                try:
                    var_value = do_var_creator()
                    if var_value is None:
                        raise ValueError(...)
                    setattr(g, var_name, var_value)
                    return var_value
                except Exception as e:
                    setattr(g, var_name, _CREATION_FAILED)
                    raise RuntimeError(f"Scoped variable creator {do_var_creator} raised an exception [{e}].")

    elif not hasattr(g, var_name):
        try:
            var_value = do_var_creator()
            if var_value is None:
                raise ValueError(f"{do_var_creator} returned None for `{var_name}`.")
            setattr(g, var_name, var_value)
            local_sidekick().display.info(f"{var_name} create of type: {type(var_value)}")
        except Exception as e:
            raise RuntimeError(f"Scoped variable creator {do_var_creator} raised an exception [{e}].")

        return var_value
    else:
        var_value = getattr(g, var_name)
        print(f"{var_name} data found.")
        return var_value


# App User
# -----------
def __get_app_user() -> Optional["AppUser"]:
    from ..helpers.pw_helper import is_someone_logged
    from ..private.AppUser import AppUser

    """
    Info of the logged user or None if no one is logged
    """
    if is_someone_logged():
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
def __prepare_user_seps() -> "UserSepsRtn":

    from ..models.private import MgmtSepsUser
    from ..private.UserSep import UserSep
    from ..private.sep_icon import do_icon_get_url
    from ..helpers.pw_helper import is_someone_logged
    from ..helpers.py_helper import class_to_dict

    user_id: int = current_user.id if is_someone_logged() else -1

    try:
        try:
            local_sidekick().display.debug("user_sep start creation...")
            sep_usr_rows = MgmtSepsUser.get_user_sep_list(user_id)
        except Exception as e:
            return str(e)

        seps: List["UserSepDict"] = []
        for sep_row in sep_usr_rows:
            item = UserSep(**sep_row)
            item.icon_url = do_icon_get_url(item.icon_file_name, item.id)
            dic = class_to_dict(item)
            # as `g` only saves 'simple' classes convert it to a Dict
            seps.append(dic)

    finally:
        local_sidekick().display.debug("user_sep was created.")

    return seps


def __get_user_seps() -> "UserSepList":
    from ..private.UserSep import UserSep

    result = []
    if app_user is None:
        local_sidekick().display.error("No current user to retrieve SEP data.")
    else:  # convert simple dict to UserSep again
        list_dic = __get_scoped_var("_user_seps", __prepare_user_seps)
        if list_dic is None or not isinstance(list_dic, list):
            local_sidekick().display.error(
                f"An error occurred getting sep from user {app_user.id}: [{type(list_dic)}] → {str(list_dic)}."
            )
        else:
            result: "UserSepList" = [UserSep(**item) for item in list_dic]

    return result


# =========================================================
# Proxies
# =========================================================

app_user: "AppUser" = LocalProxy(__get_app_user)
user_seps: "UserSepsRtn" = LocalProxy(__get_user_seps)
jinja_user: Optional["JinjaUser"] = LocalProxy(__get_jinja_user)


def __getattr__(name):
    """Dynamically resolves 'sidekick' to retrieve the current value of global_sidekick."""
    if name == "sidekick":
        from carranca import global_sidekick

        if global_sidekick is None:
            raise RuntimeError(
                "🚨 Application accessed before initialization. global_sidekick is None. "
                "Check import order or application setup."
            )
        return global_sidekick

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Keep __setattr__ to enforce read-only status
def __setattr__(name, value):
    if name == "sidekick":
        raise AttributeError(f"Cannot assign to attribute '{name}' of module '{__name__}'. It is read-only.")
    globals()[name] = value
