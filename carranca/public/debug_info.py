"""
Debug Info
Debug information

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore sqlalchemy
from typing import List, Tuple
from ..config.DynamicConfig import DynamicConfig


def get_debug_info(app, config: DynamicConfig) -> List[Tuple[str, str]]:
    from ..helpers.py_helper import coalesce, is_str_none_or_empty
    from os import getcwd
    from flask import __version__ as flask_version
    from jinja2 import __version__ as jinja2_version
    from platform import python_version, uname
    from sqlalchemy import __version__ as sqlalchemy_v
    from flask_login import __version__ as flask_login_version

    """App & and main packages version"""
    result = []
    ml = 0
    vl = 0

    def _add(name, value):
        nonlocal ml, vl  # int, float, bool, str, tuples... are immutables
        ml = len(name) if ml < len(name) else ml
        v = str(value)
        vl = len(v) if vl < len(v) else vl
        result.append((name, v))

    _add(f"{config.APP_NAME} Configuration", "")
    _add("Version", config.APP_VERSION)
    _add("Mode", config.APP_MODE)
    _add("Debug", config.APP_DEBUGGING)
    _add("Debug Messages", config.APP_DISPLAY_DEBUG_MSG)
    _add("Logging to File", config.LOG_FILE_STATUS)

    _add("Page Compression", config.APP_UNMINIFIED)
    _add("App  folder", config.APP_FOLDER)
    _add("Database address", config.SQLALCHEMY_DATABASE_URI)
    _add("Server 'name'", config.SERVER_ADDRESS)
    _add("External address ", coalesce(config.SERVER_EXTERNAL_IP, "<set on demand>"))
    _add("External port", coalesce(config.SERVER_EXTERNAL_PORT, "<none>"))

    _add("Main versions", "")
    _add("OS", f"{uname().system} v {uname().version} on {uname().node}")
    _add("Python", python_version())
    _add("Flask Login", flask_login_version)
    _add("SQLAlchemy", sqlalchemy_v)
    _add("Jinja2", jinja2_version)
    _add("Flask", flask_version)

    _add("Flask", "")
    _add("Name", app.name)
    _add("DEBUG", app.debug)
    _add("TESTING", app.testing)
    _add("SECRET_KEY", ("" if is_str_none_or_empty(app.secret_key) else "*" * 11))
    _add("Root Path", app.root_path)
    _add("Template Folder", app.template_folder)
    _add("Static Folder", app.static_folder)
    _add("Current working dir", getcwd())

    # urgente
    # for name, value in result:
    #     kind, v = (
    #         (sidekick.display.Kind.SIMPLE, ": " + value)
    #         if value
    #         else (sidekick.display.Kind.INFO, "_" * vl)
    #     )
    #     sidekick.display.print(kind, f"{name.rjust(ml)}{v}", "", False)

    # max_len_first = max(len(first) for first, _ in tuples)
    # max_len_second = max(len(second) for _, second in tuples)

    return result


# eof
