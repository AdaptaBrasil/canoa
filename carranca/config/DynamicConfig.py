"""
Equipe da Canoa -- 2024

Configuration Files for the Application

mgd 2024-05-06
mgd 2024-05-21: Base, Debug, Production
mgd 2024-10-11: Base went to it's own file
"""

# cSpell:ignore UNMINIFIED SQLALCHEMY searchpath

from os import environ
from hashlib import sha384

from .BaseConfig import BaseConfig, app_mode_development, app_mode_production, app_mode_stage
from ..common.app_constants import APP_NAME, APP_VERSION
from ..common.igniter import Fuse
from ..helpers.py_helper import as_bool, is_str_none_or_empty, get_envvar_prefix
from ..helpers.wtf_helper import LenValidate


# Get the Jinja Template folder name
def _get_template_folder():
    from jinja2 import Environment, FileSystemLoader

    # Create a Jinja2 environment using a specific template folder
    env = Environment(loader=FileSystemLoader("templates"))
    # Access the template folder path
    template_folder = env.loader.searchpath[0]
    return template_folder


# Environment Variables for the config
def _init_envvar_of_config(cfg: "DynamicConfig", fuse: Fuse):
    """
    Initialize BaseConfig
    from environment variables
    """
    from .BaseConfig import CONFIG_MANDATORY_KEYS

    envvar_prefix = get_envvar_prefix()
    t = str(True).lower()
    f = str(False).lower()
    for key, value in environ.items():
        attribute_name = key[len(envvar_prefix) :]
        if not key.upper().startswith(envvar_prefix):
            pass
        elif not hasattr(cfg, attribute_name):
            fuse.display.debug(
                f"Environment variable [{attribute_name}] is not a recognized attribute of `Config`, skipping."
            )
        elif not is_str_none_or_empty(value):
            _value = as_bool(value) if value.lower() in [t, f, "t", "1"] else value
            setattr(cfg, attribute_name, _value)
        elif is_str_none_or_empty(getattr(cfg, attribute_name, None)):
            msg = f"Config.{attribute_name} has no default value, and no value was provided."
            if attribute_name in CONFIG_MANDATORY_KEYS:
                fuse.display.error(msg)
            else:
                fuse.display.warn(msg)
        else:
            fuse.display.warn(
                f"Empty value for environment variable [{attribute_name}] ignored, retaining original value."
            )


class DynamicConfig(BaseConfig):
    APP_MODE = None

    def __init__(self, fuse: Fuse, app_debug: bool, app_propagate_debug: bool, server_address: str):
        self.APP_DEBUG = app_debug
        self.APP_PROPAGATE_DEBUG = app_propagate_debug
        self.SERVER_ADDRESS = server_address
        self.EMAIL_REPORT_CC = ""

        # flask has config.from_prefixed_env() that us used in create_app
        # but I need one now, and displaying some msg.
        _init_envvar_of_config(self, fuse)
        fuse.display.info(f"The Config class was instantiated in {self.APP_MODE} mode.")
        self.TEMPLATES_FOLDER = _get_template_folder()

        # self.DB_HELPER = {} tying to group vars for db, eg DB_len_val
        # Functions to help DB/Forms TODO: send to models
        # min & max text length for pw & user_name
        self.DB_len_val_for_pw = LenValidate(6, 22)
        self.DB_len_val_for_uname = LenValidate(3, 22)
        self.DB_len_val_for_email = LenValidate(8, 60)

        # propagate APP_DEBUG
        default = self.APP_DEBUG if self.APP_PROPAGATE_DEBUG else False

        def _if_debug(value):
            return default if value is None else as_bool(value)

        self.TESTING = _if_debug(self.TESTING)  # Flask
        self.APP_UNMINIFIED = _if_debug(self.APP_UNMINIFIED)  #
        self.DEBUG_TEMPLATES = _if_debug(self.DEBUG_TEMPLATES)  # jinja
        self.DEBUG_RENDERED_TEMPLATES = _if_debug(self.DEBUG_RENDERED_TEMPLATES)
        self.APP_DISPLAY_DEBUG_MSG = _if_debug(self.APP_DISPLAY_DEBUG_MSG)

        if is_str_none_or_empty(self.SECRET_KEY):
            """
            SECRET_KEY
            used for securely signing the session cookie (mgd: change every version)
            https://flask.palletsprojects.com/en/latest/config/#SECRET_KEY
            """
            unique = f"{APP_NAME} v{APP_VERSION}".encode()
            self.SECRET_KEY = sha384(unique).hexdigest()

    # @property
    # def DB_HELPER(self):
    #     return self._db_helper


# ===[1] Development Config
class DevelopmentConfig(DynamicConfig):
    """
    The Debug Configuration Class for the App
    """

    APP_MODE = app_mode_development

    def __init__(self, fuse: Fuse):
        super().__init__(fuse, True, True, "127.0.0.1:50090")


# ===[2] Stage Config
class StageConfig(DynamicConfig):
    """
    The Staged Configuration Class for the App
    non-production feature validation, reproduce platform-specific bugs and validate DB migrations/deploys.
    """

    APP_MODE = app_mode_stage

    def __init__(self, fuse: Fuse):
        super().__init__(fuse, False, False, "192.168.0.1:5002")


# ===[3] Production Config
class ProductionConfig(DynamicConfig):
    """
    The Production Configuration Class for the App
    """

    APP_MODE = app_mode_production

    def __init__(self, fuse: Fuse):
        super().__init__(fuse, False, False, "192.168.0.1:54454")


# Config factory by mode, add others
def get_config_for_mode(app_mode: str, fuse: Fuse) -> DynamicConfig:
    """
    Return the appropriated Configuration
    """
    match app_mode:
        case ProductionConfig.APP_MODE:
            config = ProductionConfig(fuse)
        case DevelopmentConfig.APP_MODE:
            config = DevelopmentConfig(fuse)
        case StageConfig.APP_MODE:
            config = StageConfig(fuse)
        case _:
            raise ValueError(f"Unknown app_mode: {app_mode!r}")

    return config


# eof
