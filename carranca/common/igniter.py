"""
#igniter.py
   Common classes initializer and
   basic configuration validator module

   Equipe da Canoa -- 2024
   mgd 2024-10-01--07
"""

# cSpell:ignore sqlalchemy app_name cssless sendgrid ENDC psycopg2 mandatories

from typing import Tuple
from flask import Flask
from os import path

from .Args import Args
from .app_constants import APP_NAME
from ..helpers.py_helper import is_str_none_or_empty

_error_msg = "[{0}]: An error occurred while {1}. Message: `{2}`."
fuse = None


# ---------------------------------------------------------------------------- #
# Escape Door
def _log_and_exit(ups: str):
    if fuse and fuse.display:
        fuse.display.error(ups)
    exit(ups)


# ---------------------------------------------------------------------------- #
# Fuse a igniter helper
class Fuse:
    from .Display import Display

    def __init__(self, app_name, display: Display, args: Args):
        from ..config.BaseConfig import app_mode_production, app_mode_development

        self.app_name = app_name
        self.debugging = args.app_debug
        self.display = display
        self.args = args

        if is_str_none_or_empty(args.app_mode):
            self.app_mode = app_mode_development if args.app_debug else app_mode_production
        else:
            self.app_mode = self.args.app_mode


# ---------------------------------------------------------------------------- #
def _get_debug_2() -> bool:

    # Configuration priority (debug as am example):
    # 1. Command-line argument (sys.argv): --debug
    # 2. Environment: CANOA_DEBUG
    # 3. Config: config.APP_DEBUG
    # 4. Code default values
    # Considerations:
    #    In this project, there are several configs
    #    available, of which one is selected according to
    #    the 'app_mode' argument (: 'D', 'P', etc, see config.py).
    #    Taking this inb consideration, we skip 3. Config
    #
    from ..helpers.py_helper import get_envvar

    debug_4 = False
    debug_3 = debug_4  # Read above 'Considerations'
    debug_2 = bool(get_envvar("debug", debug_3))
    return debug_2


# ---------------------------------------------------------------------------- #
def _start_fuse(app_name: str, args: Args, started_from: float) -> Tuple[any, str]:
    """
    Create the 'fuse' that will assists the initializations of classes
    """
    import json

    msg_error = None
    new_fuse = None
    try:
        from .Display import Display

        display = Display(
            f"{app_name}: ",
            args.display_mute,
            args.display_debug,
            args.display_icons,
            started_from,
        )
        new_fuse = Fuse(app_name, display, args)
        new_fuse.display.info(
            f"The 'fuse' was started in {new_fuse.app_mode} mode (and now we have how to print pretty)."
        )
        args = f"{app_name}'s args: {{0}}"
        if new_fuse.debugging:
            _args = f"\n{json.dumps(new_fuse.args.__dict__, indent=3, sort_keys=True)}"
            new_fuse.display.debug(args.format(_args))
        else:
            new_fuse.display.info(args.format(new_fuse.args))
    except Exception as e:
        new_fuse = None
        msg_error = _error_msg.format(__name__, "starting the fuse", str(e))

    return new_fuse, msg_error


# ---------------------------------------------------------------------------- #
from ..config.DynamicConfig import DynamicConfig


def _ignite_config(fuse: Fuse) -> Tuple[DynamicConfig, str]:
    """
    Select the config, based in the app_mode (production or debug)
    WARNING: Don't run with debug turned on in production!
    """
    Config = None  # this config will later be shared by sidekick
    msg_error = None
    try:
        from ..config.DynamicConfig import get_config_for_mode

        Config = get_config_for_mode(fuse.app_mode, fuse)
        if Config is None:
            raise Exception(f"Unknown config mode '{fuse.app_mode}'.")

        if not path.isfile(path.join(Config.APP_FOLDER, "main.py")):
            raise Exception("main.py file not found in the app folder. Check BaseConfig.APP_FOLDER.")

        Config.APP_DEBUGGING = True if fuse.debugging else Config.APP_DEBUG
        Config.APP_ARGS = fuse.args
        fuse.display.info(f"The app config, in '{fuse.app_mode}' mode, was ignited.")
    except Exception as e:
        msg_error = _error_msg.format(
            __name__, f"initializing the app config in mode '{fuse.app_mode}'", str(e)
        )

    return Config, msg_error


# ---------------------------------------------------------------------------- #
def _check_mandatory_keys(config, fDisplay) -> str:
    """Check if the mandatories environment variables are set."""

    msg_error = None
    try:
        from ..config.BaseConfig import CONFIG_MANDATORY_KEYS

        def __is_empty(key: str) -> bool:
            value = getattr(config, key, "")
            empty = value is None or value.strip() == ""
            if empty:
                fDisplay.error(f"[{__name__}]: Config[{config.APP_MODE}].{key} has no value.")
            return empty

        has_empty = False
        empty_keys = ""
        for key in CONFIG_MANDATORY_KEYS:
            if __is_empty(key):
                empty_keys = f"{empty_keys}{key},"
                has_empty = True

        msg_error = (
            None
            if not has_empty
            else _error_msg.format(
                __name__,
                f"confirming the existence of the mandatory configuration keys {CONFIG_MANDATORY_KEYS}",
                f"Missing: {empty_keys.strip(',')} As Environment Variable must be prefixed with {APP_NAME}.",
            )
        )

    except Exception as e:
        msg_error = _error_msg.format(
            __name__, f"checking mandatory keys of config[`{config.APP_MODE}`]", e
        )

    return msg_error


# ---------------------------------------------------------------------------- #
def _ignite_server_name(config) -> Tuple[any, str]:
    """Confirm validity of the server address"""
    msg_error = None
    try:
        from collections import namedtuple
        from urllib.parse import urlparse

        Address = namedtuple("Address", "host, port")

        try_url = f"http://{config.SERVER_ADDRESS}"
        url = urlparse(try_url)

        address = Address(url.hostname, url.port)
        if is_str_none_or_empty(address.host) or (address.port == 0):
            msg_error = f"Invalid host or port address found in [{config.SERVER_ADDRESS}], parsed: {address.host}:{address.port}`."
        else:
            config.SERVER_ADDRESS = f"{address.host}:{address.port}"
            scheme = (
                ""
                if is_str_none_or_empty(config.PREFERRED_URL_SCHEME)
                else f"{config.PREFERRED_URL_SCHEME}://"
            )
            # Flask Config
            config.RUN_HOST = address.host
            config.RUN_PORT = address.port
            fuse.display.info(f"The Flask Server address was set to '{scheme}{config.SERVER_ADDRESS}'.")

    except Exception as e:
        fuse.display.error(f"`urlparse({try_url}) -> parsed: {address.host}:{address.port}`")
        msg_error = _error_msg.format(
            __name__,
            f"parsing server address. Expect value is [HostName:Port], found: [{config.SERVER_ADDRESS}]",
            e,
        )

    return address, msg_error


# ---------------------------------------------------------------------------- #
def ignite_log_file(config: DynamicConfig, app: Flask) -> Tuple[str, str]:
    import logging

    if not config.LOG_TO_FILE:
        return "", logging.NOTSET

    from os import path
    from ..helpers.user_helper import get_unique_filename
    from logging.handlers import RotatingFileHandler
    from ..helpers.file_helper import folder_must_exist

    msg_error = None
    full_name = ""
    task = "file_name"
    # https://www.adventuresinmachinelearning.com/flask-logging-the-ultimate-guide-for-developers/
    try:
        file_name = config.LOG_FILE_NAME
        if is_str_none_or_empty(file_name):
            file_name = get_unique_filename(f"{config.APP_NAME}_", ".log")
            config.LOG_FILE_NAME = file_name

        task = "file_folder"
        file_folder = config.LOG_FILE_FOLDER
        if is_str_none_or_empty(file_folder):
            file_folder = "log_files"
            config.LOG_FILE_FOLDER = file_folder

        if not folder_must_exist(file_folder):
            msg_error = f"Cannot create log's files folder [{file_folder}]."
        else:
            task = "full_name"
            full_name = path.join(".", config.LOG_FILE_FOLDER, file_name)

            task = "level"
            s_level = logging._levelToName[config.LOG_MIN_LEVEL]

            task = "handler"
            handler = RotatingFileHandler(full_name, maxBytes=10000, backupCount=1)
            handler.setLevel(config.LOG_MIN_LEVEL)
            app.logger.addHandler(handler)
    except Exception as e:
        msg_error = f"Cannot create log's {task}: [{e}]"

    if not is_str_none_or_empty(msg_error):
        _log_and_exit(msg_error)

    return full_name, s_level


# - ---------------------------------------------------------------------------- #
# - Public --------------------------------------------------------------------- #
# - ---------------------------------------------------------------------------- #
from .Sidekick import Sidekick


def ignite_sidekick(app_name, start_at) -> Tuple[Sidekick, bool]:
    global fuse

    debug_2 = _get_debug_2()
    args = Args(debug_2).from_arguments()

    fuse, error = _start_fuse(app_name, args, start_at)
    if error:
        _log_and_exit(error)
    fuse.display.debug("The fuse was created.")

    # Config
    config, error = _ignite_config(fuse)
    if error:
        _log_and_exit(error)
    fuse.display.debug(f"Config was ignited, debugging is {config.APP_DEBUGGING}.")

    # Mandatory Configuration keys
    error = _check_mandatory_keys(config, fuse.display)
    if error:
        _log_and_exit(error)
    fuse.display.debug("All mandatory configuration keys were informed.")

    # Server Address
    _, error = _ignite_server_name(config)
    if error:
        _log_and_exit(error)
    fuse.display.debug("Flask's Server Name is ready and configured.")

    # Create the session shared 'sidekick'
    sidekick = Sidekick(config, fuse.display)
    fuse.display.info("The 'sidekick' was ignited.")

    # ---------------------------------------------------------------------------- #
    # Give warnings of import configuration that may be missing
    from ..helpers.py_helper import is_str_none_or_empty

    warns = 0
    if is_str_none_or_empty(config.EMAIL_API_KEY):
        warns += 1
        fuse.display.warn(f"Sendgrid API key was not found, the app will not be able to send emails.")

    if is_str_none_or_empty(config.EMAIL_ORIGINATOR):
        warns += 1
        fuse.display.warn(
            f"The app email originator is not defined, the app will not be able to send emails."
        )

    # ---------------------------------------------------------------------------- #
    # Final message

    fuse.display.info(f"{__name__} module completed with 0 errors and {warns} warnings.")
    display_mute_after_init = fuse.args.display_mute_after_init

    del fuse  # clean up fuse to prevent memory leaks

    return sidekick, display_mute_after_init


# - ---------------------------------------------------------------------------- #
def ignite_sql_connection(sidekick, uri):

    from sqlalchemy import create_engine, select

    try:
        engine = create_engine(uri)
        with engine.connect() as connection:
            connection.scalar(select(1))
            sidekick.display.info("The database connection is active.")

    except Exception as e:
        _log_and_exit(f"Unable to connect to the database. Error details: [{e}].")

    return


# eof
