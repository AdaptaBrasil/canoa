"""
#igniter.py
   Common classes initializer and
   basic configuration validator module

   Equipe da Canoa -- 2024
   mgd 2024-10-01--07
"""

# cSpell:ignore sqlalchemy app_name cssless sendgrid ENDC mandatories elap abbrs

# -- ⚠️ ----------------------------------
# This module uses `local imports`
# (within functions) to increase  modularization
# and focus, clarity of function dependencies,
# explicit dependency management and readability.
# It is only run once.

import time, os.path as path
from typing import Tuple, Optional


from .Args import Args
from .app_constants import APP_NAME
from ..helpers.py_helper import get_envvar, get_envvar_prefix, is_str_none_or_empty
from .app_error_assistant import RaiseIf
from ..helpers.email_helper import EmailProvider

_ERROR_MSG = "[{}]: An error occurred while {}. Message: `{}`."
_DV_WAIT_SECONDS = 10  # max wait for the data_validate version lookup (dv_version_helper), before the final message
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
        self.app_name = app_name
        self.debugging = args.app_debug
        self.display = display
        self.args = args

        # App mode priority: 1. argument, 2. env CANOA_APP_MODE (set in rema.sh). There is no default:
        # the app does not start without it. Case-insensitive, the upper case value selects one of the existing modes.
        modes = {mode.upper(): mode for mode in (APP_MODE_PRODUCTION, APP_MODE_DEVELOPMENT, APP_MODE_STAGE)}
        valid_modes = ", ".join(modes.values())
        env_name = f"{get_envvar_prefix()}APP_MODE"
        app_mode = get_envvar("APP_MODE") if is_str_none_or_empty(args.app_mode) else args.app_mode
        if is_str_none_or_empty(app_mode):
            raise ValueError(f"{env_name} is not set. Select one of: [{valid_modes}].")

        selected_mode = modes.get(str(app_mode).strip().upper())
        if selected_mode is None:
            raise ValueError(f"Unknown {env_name} '{app_mode}'. Select one of: [{valid_modes}].")

        self.app_mode: str = selected_mode


# ---------------------------------------------------------------------------- #
def _get_debug_2() -> bool | None:

    # Configuration priority (debug as am example):
    # 1. Command-line argument (sys.argv): --app_debug
    # 2. Environment: CANOA_DEBUG
    # 3. Config: config.APP_DEBUG (the selected mode's own default)
    # 4. Code default values
    # Considerations:
    #    In this project, there are several configs
    #    available, of which one is selected according to
    #    the 'app_mode' argument (: 'D', 'P', etc, see config.py).
    #    At this point no config is selected yet, so 2. returns None when
    #    CANOA_DEBUG is not set, and DynamicConfig falls back to 3.
    #
    from ..helpers.py_helper import get_envvar, as_bool

    debug_2 = get_envvar("DEBUG", None)
    return None if is_str_none_or_empty(debug_2) else as_bool(debug_2)


# ---------------------------------------------------------------------------- #
def _start_fuse(app_name: str, args: Args, started_from: float) -> Tuple[Fuse | None, str]:
    """
    Create the 'fuse' that will assists the initializations of classes
    """
    import json

    msg_error = ""
    _fuse: Fuse | None = None
    try:
        from .Display import Display

        display = Display(
            f"{app_name}: ",
            args.display_mute,
            args.display_debug,
            args.display_icons,
            started_from,
        )
        _fuse = Fuse(app_name, display, args)
        _fuse.display.info(f"The 'fuse' was started in {_fuse.app_mode} mode (and now we have how to print pretty).")
        s_args = f"{app_name}'s args: {{0}}"
        if _fuse.debugging:
            _args = f"\n{json.dumps(_fuse.args.__dict__, indent=3, sort_keys=True)}"
            _fuse.display.debug(s_args.format(_args))
        else:
            _fuse.display.info(s_args.format(_fuse.args))
    except Exception as e:
        _fuse = None
        msg_error = _ERROR_MSG.format(__name__, "starting the fuse", str(e))

    return _fuse, msg_error


# ---------------------------------------------------------------------------- #
from ..config.DynamicConfig import DynamicConfig, APP_MODE_DEVELOPMENT, APP_MODE_PRODUCTION, APP_MODE_STAGE


def _ignite_config(fuse: Fuse, flask_app_name: str) -> Tuple[DynamicConfig | None, str]:
    """
    Select the config, based in the app_mode (production or debug)
    WARNING: Don't run with debug turned on in production!
    """

    config = None
    msg_error = ""
    try:
        from ..config.DynamicConfig import get_config_for_mode

        config = get_config_for_mode(fuse.app_mode, fuse)
        if config is None:
            raise Exception(f"Unknown config mode '{fuse.app_mode}'.")

        if not path.isfile(path.join(config.APP_PATH, flask_app_name)):
            raise Exception(f"{flask_app_name} file not found in the app folder. Check BaseConfig.APP_PATH.")

        # fuse.debugging (--app_debug | CANOA_DEBUG) was already applied to config.APP_DEBUG by DynamicConfig
        config.APP_DEBUGGING = config.APP_DEBUG
        # REMOVE config.APP_ARGS = fuse.args
        fuse.display.info(f"The app config, in '{fuse.app_mode}' mode, was ignited.")
    except Exception as e:
        msg_error = _ERROR_MSG.format(__name__, f"initializing the app config in mode '{fuse.app_mode}'", str(e))

    return config, msg_error


# ---------------------------------------------------------------------------- #
def _check_mandatory_keys(config, fDisplay) -> str:
    """Check if the mandatories environment variables are set."""

    msg_error = ""
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
            ""
            if not has_empty
            else _ERROR_MSG.format(
                __name__,
                f"confirming the existence of the mandatory configuration keys: [{CONFIG_MANDATORY_KEYS}]",
                f"Missing: [{empty_keys.strip(',')}]. Note that environment variables must be prefixed with '{APP_NAME}'.",
            )
        )

    except Exception as e:
        msg_error = _ERROR_MSG.format(__name__, f"checking mandatory keys of config[`{config.APP_MODE}`]", e)

    return msg_error


# ---------------------------------------------------------------------------- #
def _ignite_sql_connection(fuse: Fuse, uri: str) -> Tuple[str, str, str]:
    """
    Establish a connection to the database and retrieve the database version and schema.

    Args:
        uri (str): The database connection URI.

    Returns:
        Tuple[str, str, str]: error message (if any), database version and
        the schema the server resolved (search_path), e.g. canoa or canoa_dev.
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError

    error = ""
    db_version: str = "?"
    db_schema: str = "?"
    fuse.display.debug("Connecting to the database.")  # this may take a while
    error_msg = "{} error: Unable to connect to the database.{}\nError details:\n[{}]."
    try:
        engine = create_engine(uri)
        start_time = time.time()
        with engine.connect() as connection:
            result = connection.execute(text("select number, current_schema() from db_version order by id desc limit 1"))
            row = result.first()
            db_version = row[0] if row and isinstance(row[0], str) else "!"
            db_schema = row[1] if row and isinstance(row[1], str) else "!"
            elap = f"{(time.time() - start_time) * 1000:,.2f}"
            fuse.display.info(f"Connected to database version {db_version} (schema {db_schema}) successfully in {elap} ms.")
    except OperationalError as e:
        error = error_msg.format("Operational", f"\nuri: [{uri}]", e)
    except Exception as e:
        error = error_msg.format("Unexpected", "", e)

    return error, db_version, db_schema


# ---------------------------------------------------------------------------- #
def _check_roles_abbr(fuse: Fuse, uri: str) -> str:
    """
    Confirm that every `abbr` in the `roles` table has a matching member
    in `carranca.private.RolesAbbr.RolesAbbr`, catching DB/code drift early.
    """
    from sqlalchemy import create_engine, text
    from ..private.RolesAbbr import RolesAbbr

    error = ""
    try:
        engine = create_engine(uri)
        with engine.connect() as connection:
            result = connection.execute(text("select abbr from roles"))  # avoid schema: from canoa.roles"))
            db_abbrs = {row[0].strip() for row in result}

        known_abbrs = {r.value for r in RolesAbbr}
        unknown_abbrs = db_abbrs - known_abbrs

        if unknown_abbrs:
            error = _ERROR_MSG.format(
                __name__,
                "checking roles.abbr against RolesAbbr",
                f"DB has abbr(s) {sorted(unknown_abbrs)} not present in RolesAbbr. Update carranca/private/RolesAbbr.py.",
            )
        else:
            fuse.display.debug(f"All {len(db_abbrs)} role abbreviations in the DB match RolesAbbr (in RolesAbbr.py).")
    except Exception as e:
        error = _ERROR_MSG.format(__name__, "checking table roles.abbr against RolesAbbr.py", str(e))

    return error


# - ---------------------------------------------------------------------------- #
# - Public --------------------------------------------------------------------- #
# - ---------------------------------------------------------------------------- #
from .Sidekick import Sidekick


def ignite_app(app_name: str, flask_app_name: str, start_at: float) -> Tuple[Sidekick, str, str, bool]:
    from .Display import Display

    global fuse
    warns = 0
    errors = 0

    debug_2 = _get_debug_2()
    args = Args(debug_2).from_arguments()

    fuse, error = _start_fuse(app_name, args, start_at)
    if error:
        _log_and_exit(error)

    assert fuse is not None  # this is  JUST for the type checker
    fuse.display.debug("The fuse was created.")

    # Config
    config, error = _ignite_config(fuse, flask_app_name)
    if error:
        _log_and_exit(error)

    assert config is not None  # this is  JUST for the type checker

    fuse.display.debug(f"Config was ignited, debugging is {config.APP_DEBUGGING}.")

    # Mandatory Configuration keys
    error = _check_mandatory_keys(config, fuse.display)
    if error:
        _log_and_exit(error)
    fuse.display.debug("All mandatory configuration keys were informed.")

    # Check DB connection, stop if not debugging
    error, db_version, db_schema = _ignite_sql_connection(fuse, config.SQLALCHEMY_DATABASE_URI)
    if not error:
        fuse.display.info(
            f"SQLAlchemy engine was created and the db (version {db_version}) connection to [{db_schema}] was successfully tested."
        )
    elif RaiseIf.ignite_no_sql_conn:
        _log_and_exit(error)
    else:
        errors += 1
        fuse.display.error(error)

    # Check that all DB role abbreviations are known to RolesAbbr
    error = _check_roles_abbr(fuse, config.SQLALCHEMY_DATABASE_URI)
    if error:
        if RaiseIf.ignite_roles_mismatch:
            _log_and_exit(error)
        else:
            errors += 1
            fuse.display.error(error)

    # Create the session shared 'sidekick'
    sidekick = Sidekick(config, fuse.display)
    fuse.display.info("The 'sidekick' was ignited.")

    # data_validate's version, read in the background while the next steps run (waited for before the final message)
    from .. import global_dv_info  # imported here: the package imports this module
    from ..helpers.dv_version_helper import start_dv_version_lookup, dv_app_and_path

    dv_app, dv_path = dv_app_and_path(config)
    dv_thread = start_dv_version_lookup(sidekick, global_dv_info, dv_path, dv_app.ui_name)

    # ---------------------------------------------------------------------------- #
    # Give warnings of import configuration that may be missing

    no_email_text = "The email {0} for the app is not defined. The app will not be able to send emails."

    no_email = not hasattr(config, "EMAIL_PROVIDER") or (config.EMAIL_PROVIDER == EmailProvider.NO_EMAIL.value)
    if no_email:
        config.EMAIL_PROVIDER = EmailProvider.NO_EMAIL.value
    else:
        if is_str_none_or_empty(config.EMAIL_API_KEY_PW):
            warns += 1
            fuse.display.warn(no_email_text.format("API key/password"))

        if is_str_none_or_empty(config.EMAIL_ORIGINATOR):
            warns += 1
            fuse.display.warn(no_email_text.format("originator"))

    # ---------------------------------------------------------------------------- #
    # data_validate's version: not reading it is a warning
    dv_thread.join(timeout=_DV_WAIT_SECONDS)
    if dv_thread.is_alive():
        warns += 1
        fuse.display.warn(f"The {dv_app.ui_name} version is still being read, it was waited for {_DV_WAIT_SECONDS}s.")
    elif not global_dv_info.ready:
        warns += 1  # the thread already displayed the reason

    # ---------------------------------------------------------------------------- #
    # Final message

    fuse.display.print(
        (Display.Kind.INFO if warns + errors == 0 else (Display.Kind.WARN if errors == 0 else Display.Kind.ERROR)),
        f"[{__name__}] module completed with {errors} error{'' if errors == 1 else 's'} and {warns} warning{'' if warns == 1 else 's'}."
        f" {dv_app.ui_name} version: {global_dv_info.version}.",
    )
    mute_display_after_init = fuse.args.display_mute_after_init

    del fuse  # clean up fuse to prevent memory leaks

    return sidekick, db_version, db_schema, mute_display_after_init


# eof
