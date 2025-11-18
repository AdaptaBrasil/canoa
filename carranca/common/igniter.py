"""
#igniter.py
   Common classes initializer and
   basic configuration validator module

   Equipe da Canoa -- 2024
   mgd 2024-10-01--07
"""

# cSpell:ignore sqlalchemy app_name cssless sendgrid ENDC mandatories

# -- ⚠️ ----------------------------------
# This module uses `local imports`
# (within functions) to increase  modularization
# and focus, clarity of function dependencies,
# explicit dependency management and readability.
# It is only run once.

import time, os.path as path
from typing import Tuple, NamedTuple, Optional, Any
from urllib.parse import urlparse

from .Args import Args
from .app_constants import APP_NAME
from .app_error_assistant import RaiseIf
from ..helpers.py_helper import is_str_none_or_empty

_ERROR_MSG = "[{}]: An error occurred while {}. Message: `{}`."
fuse: Optional["Fuse"] = None


# ---------------------------------------------------------------------------- #
# Escape Door, use display after sidekick is created
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
            self.app_mode = app_mode_stage
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
    debug_2 = bool(get_envvar("debug", str(debug_3)))
    return debug_2


# ---------------------------------------------------------------------------- #
def _start_fuse(app_name: str, args: Args, started_from: float) -> Tuple[Any, str]:
    """
    Create the 'fuse' that will assists the initializations of classes
    """
    import json

    msg_error = ''
    new_fuse: Optional[Fuse] = None
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
        s_args = f"{app_name}'s args: {{0}}"
        if new_fuse.debugging:
            _args = f"\n{json.dumps(new_fuse.args.__dict__, indent=3, sort_keys=True)}"
            new_fuse.display.debug(s_args.format(_args))
        else:
            new_fuse.display.info(s_args.format(new_fuse.args))
    except Exception as e:
        new_fuse = None
        msg_error = _ERROR_MSG.format(__name__, "starting the fuse", str(e))

    return new_fuse, msg_error


# ---------------------------------------------------------------------------- #
from ..config.DynamicConfig import DynamicConfig, app_mode_stage


def _ignite_config(fuse: Fuse) -> Tuple[DynamicConfig, str]:
    """
    Select the config, based in the app_mode (production or debug)
    WARNING: Don't run with debug turned on in production!
    """
    config = None  # this config will later be shared by sidekick
    msg_error = ''
    try:
        from ..config.DynamicConfig import get_config_for_mode

        config = get_config_for_mode(fuse.app_mode, fuse)
        if config is None:
            raise Exception(f"Unknown config mode '{fuse.app_mode}'.")

        if not path.isfile(path.join(config.APP_FOLDER, "main.py")):
            raise Exception(
                "main.py file not found in the app folder. Check BaseConfig.APP_FOLDER."
            )

        config.APP_DEBUGGING = True if fuse.debugging else config.APP_DEBUG
        config.APP_ARGS = fuse.args
        fuse.display.info(f"The app config, in '{fuse.app_mode}' mode, was ignited.")
    except Exception as e:
        msg_error = _ERROR_MSG.format(
            __name__, f"initializing the app config in mode '{fuse.app_mode}'", str(e)
        )

    return config, msg_error


# ---------------------------------------------------------------------------- #
def _check_mandatory_keys(config, fDisplay) -> str:
    """Check if the mandatories environment variables are set."""

    msg_error = ''
    try:
        from ..config.BaseConfig import CONFIG_MANDATORY_KEYS

        def __is_empty(key: str) -> bool:
            value = getattr(config, key, "")
            empty = value is None or value.strip() == ""
            if empty:
                fDisplay.error(
                    f"[{__name__}]: Config[{config.APP_MODE}].{key} has no value."
                )
            return empty

        has_empty = False
        empty_keys = ""
        for key in CONFIG_MANDATORY_KEYS:
            if __is_empty(key):
                empty_keys = f"{empty_keys}{key},"
                has_empty = True

        msg_error = (
            ''
            if not has_empty
            else _ERROR_MSG.format(
                __name__,
                f"confirming the existence of the mandatory configuration keys: [{CONFIG_MANDATORY_KEYS}]",
                f"Missing: [{empty_keys.strip(',')}]. Note that environment variables must be prefixed with '{APP_NAME}'.",
            )
        )

    except Exception as e:
        msg_error = _ERROR_MSG.format(
            __name__, f"checking mandatory keys of config[`{config.APP_MODE}`]", e
        )

    return msg_error


# ---------------------------------------------------------------------------- #
def _ignite_server_name(config) -> Tuple[Any, str]:
    """Confirm validity of the server address"""
    msg_error = ''

    class Address(NamedTuple):
        host: str
        port: int

    address = Address('', 0)
    try:

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
            fuse.display.info(
                f"The Flask Server address was set to '{scheme}{config.SERVER_ADDRESS}'."
            )

    except Exception as e:
        fuse.display.error(
            f"`urlparse({try_url}) -> parsed: {address.host}:{address.port}`"
        )
        msg_error = _ERROR_MSG.format(
            __name__,
            f"parsing server address. Expect value is [HostName:Port], found: [{config.SERVER_ADDRESS}]",
            e,
        )

    return address, msg_error


# ---------------------------------------------------------------------------- #
def _ignite_sql_connection(uri: str) -> Tuple[str, str]:
    """
    Establish a connection to the database and retrieve the database version.

    Args:
        uri (str): The database connection URI.

    Returns:
        Tuple[str, str]: A tuple containing an error message (if any) and the database version.
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError

    error: str = None
    db_version: str = ""
    fuse.display.debug("Connecting to the database.")  # this may take a while
    error_msg = "{} error: Unable to connect to the database. Error details: [{}]."
    try:
        engine = create_engine(uri)
        start_time = time.time()
        with engine.connect() as connection:
            result = connection.execute(
                text("select number from db_version order by id desc limit 1")
            )
            db_version = result.scalar()
            fuse.display.info(
                f"Connected to database version {db_version} successfully in {(time.time() - start_time) * 1000:,.2f} ms."
            )
    except OperationalError as e:
        error = error_msg.format("Operational", e)
    except Exception as e:
        error = error_msg.format("Unexpected", e)

    return error, db_version


# - ---------------------------------------------------------------------------- #
# - Public --------------------------------------------------------------------- #
# - ---------------------------------------------------------------------------- #
from .Sidekick import Sidekick


def ignite_app(app_name, start_at) -> Tuple[Sidekick, str, bool]:
    from .Display import Display

    global fuse
    warns = 0
    errors = 0

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

    # Check DB connection, stop if not debugging
    error, db_version = _ignite_sql_connection(config.SQLALCHEMY_DATABASE_URI)
    if not error:
        fuse.display.info(
            "SQLAlchemy engine was created and the db connection was successfully tested."
        )
    elif RaiseIf.ignite_no_sql_conn:
        _log_and_exit(error)
    else:
        errors += 1
        fuse.display.error(error)

    # Create the session shared 'sidekick'
    sidekick = Sidekick(config, fuse.display)
    fuse.display.info("The 'sidekick' was ignited.")

    # ---------------------------------------------------------------------------- #
    # Give warnings of import configuration that may be missing

    if is_str_none_or_empty(config.SENDGRID_API_KEY):
        warns += 1
        fuse.display.warn(
            "Sendgrid API key was not found, the app will not be able to send emails."
        )

    if is_str_none_or_empty(config.EMAIL_ORIGINATOR):
        warns += 1
        fuse.display.warn(
            "The app email originator is not defined, the app will not be able to send emails."
        )

    # ---------------------------------------------------------------------------- #
    # Final message

    fuse.display.print(
        (
            Display.Kind.INFO
            if warns + errors == 0
            else (Display.Kind.WARN if errors == 0 else Display.Kind.ERROR)
        ),
        f"{__name__} module completed with {errors} errors and {warns} warnings.",
    )
    display_mute_after_init = fuse.args.display_mute_after_init

    del fuse  # clean up fuse to prevent memory leaks

    return sidekick, db_version, display_mute_after_init


# eof
