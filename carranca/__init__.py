"""
Package/__init__.py
`This file is executed by the Python interpreter on startup, once`

Equipe da Canoa -- 2024
mgd

"""

# cSpell:ignore app_name sqlalchemy sessionmaker autoflush gethostname connstr juser scms

# ============================================================================ #
from flask_login import LoginManager
from sqlalchemy.orm import scoped_session

from typing import Dict, List
from .common.Sidekick import Sidekick

# App Global variables
global_sidekick: Sidekick | None = None
global_login_manager: LoginManager = None
global_sqlalchemy_scoped_session: scoped_session = None
global_ui_texts_cache: Dict[str, str] = {}
APP_DB_VERSION: str = "?"


"""
'scoped' refers to the management of SQLAlchemy `Session` objects within a specific scope,
such as a thread or a request in a web application. The `scoped_session` class provides
a way to ensure that each thread or request gets its own session, which is isolated from
sessions used by other threads or requests.

The main advantage of using `scoped_session` is that it simplifies session management in
multi-threaded or multi-request environments by automatically handling the creation
and removal of sessions based on the current scope.
"""

# Module variable
import time

started = time.perf_counter()

# Imports
import json
import jinja2
import socket

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

from .helpers.py_helper import crc16
from .private.JinjaUser import JinjaUser
from .helpers.pw_helper import is_someone_logged
from .helpers.file_helper import file_full_name_parse

# 1/3 This line produce the sidekick-incident, moved to the _register_jinja
# from .helpers.route_helper import private_route, public_route, static_route


# ============================================================================ #
# Private methods
# ---------------------------------------------------------------------------- #
def _register_blueprint_events(app: Flask):
    from .private.routes import bp_private
    from .public.routes import bp_public

    def do_after_blueprint_request(r):
        # @app.teardown_request
        # def shutdown_session(exception=None):
        # It is 'usually'define in teardown_request. but is to often, each time a
        #   "GET /static/img/pages/canoa_fundo.jpeg HTTP/1.1" 304 -
        # it shuts the session.
        try:
            if global_sqlalchemy_scoped_session.dirty:
                app.logger.error(
                    f"SqlAlchemySession is dirty. Modified instances: [{global_sqlalchemy_scoped_session.dirty}]."
                )
            else:
                app.logger.debug(
                    f"SqlAlchemySession is shutting down {('active' if global_sqlalchemy_scoped_session.is_active else 'inactive')} and clean."
                )

            cl = (int(r.headers.get("Content-Length", 0)) if r else 0) / 1000
            app.logger.debug(f"Ending secession, sending  {cl:,.2f} Kb, with response status [{r.status}].")
            global_sqlalchemy_scoped_session.remove()
        except Exception as e:
            app.logger.error(
                f"An error occurred removing the current session [{global_sqlalchemy_scoped_session}]. Error [{e}]."
            )

        return r

    bp_private.after_request(do_after_blueprint_request)
    bp_public.after_request(do_after_blueprint_request)

    return


# ---------------------------------------------------------------------------- #
def _register_blueprint_routes(app: Flask):
    from .private.routes import bp_private
    from .public.routes import bp_public

    app.register_blueprint(bp_private)
    app.register_blueprint(bp_public)

    return


# ---------------------------------------------------------------------------- #
def _register_jinja(app: Flask, debugUndefined: bool, app_name: str, app_version: str):
    from .helpers.types_helper import DBTexts
    from .helpers.uiact_helper import UiActResponseProxy
    from .helpers.route_helper import private_route, public_route, static_route
    from .helpers.js_consts_helper import js_form_sec_key, js_form_cargo_id, js_form_sec_value

    def __get_app_menu(sub_menu_name: str) -> DBTexts:
        sub_menu: DBTexts = {}
        if not is_someone_logged():
            return sub_menu

        from .helpers.ui_db_texts_helper import get_app_menu

        _app_menu = get_app_menu()
        if sub_menu_name in _app_menu:
            sub_menu_str = _app_menu[sub_menu_name]
            sub_menu = json.loads(sub_menu_str)

        return sub_menu

    def __get_jinja_user() -> JinjaUser | None:
        if is_someone_logged():  # 'import jinja_user' only when a user is logged
            from .common.app_context_vars import jinja_user

            return jinja_user
        else:
            return None

    def __get_user_sep_menu_list() -> List[Dict]:
        # Provides de sep menu
        sep_list: List[Dict] = []
        if is_someone_logged():  # 'import jinja_user' only when a user is logged
            from .common.app_context_vars import app_user

            sep_list = [{"code": user.code, "name": user.fullname} for user in app_user.seps]

        return sep_list

    def __get_scm_menu_list() -> List[Dict]:
        scm_list: List[Dict] = []
        # mgd 2025.11.09
        # if is_someone_logged():  # 'import jinja_user' only when a user is logged
        #     from .common.app_context_vars import jinja_user

        #     if jinja_user.power:
        #         from .models.private import Schema

        #         scms = Schema.get_schemas(["id", "name"])
        #         scm_list = [
        #             {"id": scm.id, "name": scm.name} for scm in scms
        #         ]  # TODO app_user.scms]

        return scm_list

    def __do_btn_id(action: str, data: str) -> str:
        if not isinstance(data, str):
            raise ValueError("Invalid argument: string expected in __do_btn_id(action: str, data: str)")
        i: int = crc16(data)
        btn_id = f"{action}{format(i, '04x')}"
        return btn_id

    app.jinja_env.globals.update(
        app_name=app_name,
        app_version=app_version,
        static_route=static_route,
        private_route=private_route,
        public_route=public_route,
        do_btn_id=__do_btn_id,
        jinja_user=__get_jinja_user,
        app_menu=__get_app_menu,
        sep_menu=__get_user_sep_menu_list,
        scm_menu=__get_scm_menu_list,
        ui_act_add=UiActResponseProxy.add,
        ui_act_shw=UiActResponseProxy.show,
        safe_token={"key": js_form_sec_key, "value": js_form_sec_value(), "cargo": js_form_cargo_id},
    )
    if debugUndefined:
        # Enable DebugUndefined for better error messages in Jinja2 templates
        app.jinja_env.undefined = jinja2.DebugUndefined
    return


# ---------------------------------------------------------------------------- #
def _do_sqlalchemy_scoped_session(uri: str) -> scoped_session:

    # https://docs.sqlalchemy.org/en/20/orm/contextual.html
    # https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/

    engine = create_engine(uri, future=True)
    new_session = sessionmaker(autocommit=False, autoflush=True, bind=engine)

    return scoped_session(new_session)


# ---------------------------------------------------------------------------- #
def _register_db(app: Flask):

    db = SQLAlchemy()
    db.init_app(app)

    return


# ---------------------------------------------------------------------------- #
def _info(text: str):  # shortcut
    global_sidekick.display.info(text)


# ---------------------------------------------------------------------------- #
def _create_app_and_log_file(app_name: str):
    from .helpers.db_helper import db_connstr_obfuscate
    from .helpers.log_helper import do_log_file

    # -- the Flask's app
    app = Flask(app_name)
    _info(f"The Flask App was created, named '{app.name}'.")

    # 🖋️ Local alias for clarity — sk rides with sidekick, no duplication.
    # from ..common.app_context_vars import sidekick
    g_sk = global_sidekick

    # -- config from file
    app.config.from_object(g_sk.config)
    # obfuscate after app is configured
    db_connstr_obfuscate(g_sk.config)
    _info("App's config was successfully bound to the app.")

    # -- config from env vars
    app.config.from_prefixed_env(app_name)
    pcName = socket.gethostname().upper()
    _info(f"App's config updated with environment variables from [{pcName}].")

    # -- Log file
    if not g_sk.config.LOG_TO_FILE:
        g_sk.config.LOG_FILE_STATUS = "off"
    else:
        cfg = g_sk.config
        error, full_name, level = do_log_file(app, cfg.LOG_FILE_NAME, cfg.LOG_FILE_FOLDER, cfg.LOG_MIN_LEVEL)
        info = f"file '{full_name}' levels '{level}' and above"
        if not error:
            _info(f"Logging to {info}.")
            app.logger.log(
                g_sk.config.LOG_MIN_LEVEL,
                f"{app.name}'s log {info} is ready.",
            )
            g_sk.config.LOG_FILE_STATUS = "ready"
            g_sk.log_filename = file_full_name_parse(full_name)[2]
        else:
            g_sk.config.LOG_FILE_STATUS = "error"
            g_sk.display.error(f"{app_name}'s log {info} creation error: [{error}].")

    return app


# ============================================================================ #
# App + helpers
def create_app():
    from .common.app_constants import APP_NAME, APP_VERSION
    from .common.igniter import ignite_app

    # ⚠️ =================================================
    # Global variables should be assigned before any other module
    # imports them. If not, they will remain None even if a value
    # is assigned before being used.

    # === 1/3 Global sidekick  === #
    global global_sidekick, APP_DB_VERSION
    # === Check if all mandatory information is ready === #
    global_sidekick, APP_DB_VERSION, display_mute_after_init = ignite_app(APP_NAME, started)
    _info(f"[{global_sidekick}] instance is now ready. It will be available during app's context.")

    # == 2/3 Global Scoped SQLAlchemy Session
    global global_sqlalchemy_scoped_session
    db_uri = str(global_sidekick.config.SQLALCHEMY_DATABASE_URI)
    global_sqlalchemy_scoped_session = _do_sqlalchemy_scoped_session(db_uri)
    db_uri = None  # is a secret
    _info("A scoped SQLAlchemy session was successfully instantiated.")

    # === Flask App, config it & file log ===`#
    app = _create_app_and_log_file(APP_NAME)

    # === 3/3 Global Jinja Login Manager
    # https://flask-login.readthedocs.io/en/latest/
    global global_login_manager
    global_login_manager = LoginManager()
    global_login_manager.init_app(app)
    _info("The Login Manager has been successfully initialized and attached to the app.")

    # -- Register SQLAlchemy
    _register_db(app)
    _info("The app was registered in SqlAlchemy.")

    # -- Register BluePrint events & routes
    _register_blueprint_events(app)
    _info("Added 'after_request' event for all blueprints.")
    _register_blueprint_routes(app)
    _info("The blueprint routes were collected and registered within the app.")

    # -- Jinja2
    _register_jinja(app, global_sidekick.config.DEBUG_TEMPLATES, APP_NAME, APP_VERSION)
    sd = f"(with debug_templates as {global_sidekick.config.DEBUG_TEMPLATES})"
    _info(f"All Jinja functions of this app have been successfully attached to 'jinja_env.globals' {sd}.")

    # config sidekick.display
    if display_mute_after_init:
        global_sidekick.display.mute_all = True

    return app, global_sidekick


# eof
