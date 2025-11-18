"""
 Equipe da Canoa -- 2024

 Configuration Files for the Application
----------------------------------------
 ⚠️ Attention
---------------------------------------
    This file position is VERY important
    `app_folder` must point to the folder
    where main.py is located



 mgd 2024-05-06
 mgd 2024-05-21: Base, Debug, Production
 mgd 2024-10-11: new file for BaseConfig, simplify imports


"""

# cSpell:ignore SQLALCHEMY UNMINIFIED searchpath

from os import path
from flask import Config
import logging

from ..common.app_constants import APP_NAME, APP_VERSION
from ..helpers.file_helper import path_remove_last_folder

CONFIG_MANDATORY_KEYS = [
    "SQLALCHEMY_DATABASE_URI",
    "SERVER_ADDRESS",
    "SECRET_KEY",
    "APP_MODE",
]

type TrueInDebug = bool | None
# === Available app/config modes, add yours own mode here (extend)
app_mode_production: str = "Production"  # capital P
app_mode_development: str = "Development"  # capital D
app_mode_stage: str = "Stage"  # capital S
# ---------------------------
# Get the folder from main.py
app_folder = path.abspath(path_remove_last_folder(path.dirname(__file__)))


# Base Class for App Config
# see https://flask.palletsprojects.com/en/latest/config/ for other attributes
class BaseConfig(Config):
    """
    The Base Configuration Class for the App
    ----------------------------------------

    For the `data_validate` process's
    parameters/configuration see: ./config_upload.py
    """

    """ App Identification
        ----------------------------
    """

    APP_NAME = APP_NAME
    APP_VERSION = APP_VERSION

    """ Canoa Configurations
        --------------------------
    """
    # This is the final debug state of the app.
    #  See _get_debug_2 & Fuse
    APP_DEBUGGING: TrueInDebug = None
    # see initialize:
    #  several keys are set to APP_PROPAGATE_DEBUG
    #  when it's config value is None
    APP_PROPAGATE_DEBUG = False
    # set in derived classes
    APP_DEBUG: TrueInDebug = None
    APP_UNMINIFIED: TrueInDebug = False  #
    APP_DISPLAY_DEBUG_MSG: TrueInDebug = None

    APP_MODE = "None"  # see below (enum)
    # see main.py, uses package `watchfiles` if --no-reload is set in launch.json
    APP_AUTO_RELOAD = True  # <- True if APP_PROPAGATE_DEBUG else False

    # UI Texts cache (to avoid multiple DB queries)
    # (see table ui_texts, UIDbTexts.py and carranca.py>global_ui_texts_cache: dict)
    # 0= no cache; -1 < 0 infinite; n > 0 = _n_ minutes
    APP_UI_DB_TEXTS_CACHE_LIFETIME_MIN = 0

    """ Helpers Configuration
        --------------------------
    """
    # Registered user on the email API
    EMAIL_ORIGINATOR = ""  # from os_environment
    EMAIL_ORIGINATOR_NAME = f"e-mail de {APP_NAME}"
    # "  with key
    SENDGRID_API_KEY = ""  # from os_environment
    # Folders
    APP_FOLDER = app_folder
    # storage area (user_files, schema_icons...)
    COMMON_PATH = path_remove_last_folder(app_folder)

    # The name of the folder for storing sensitive, non-versioned files.
    LOCAL_STORAGE_FOLDER = "LocalStorage"
    # ⚠️ CRITICAL: This path points to a directory for sensitive, non-versioned files.
    # It MUST NOT be committed to Git or any other version control system. This
    # directory is intended for confidential information such as API keys, service
    # account credentials (e.g., 'canoa-gmail-key.json'), and other secrets that
    # must never be exposed in the codebase.
    LOCAL_STORAGE_PATH = path.join(COMMON_PATH, LOCAL_STORAGE_FOLDER)

    # My address service is SERVER_EXTERNAL_IP is empty
    # (used to send recovery email confirmation, etc)
    EXTERNAL_IP_SERVICE = "https://checkip.amazonaws.com"
    # satelier.dev.br
    # SERVER_EXTERNAL_IP = "177.43.119.39"
    SERVER_EXTERNAL_PORT = ""

    """ Flask Configuration
        --------------------------
        https://flask.palletsprojects.com/en/latest/config/
        this must be set individually for each APP_MODE (see config.py)
        to send envvars directly to flask use the FLASK_ prefix
    """
    DEBUG: TrueInDebug = None  # <- True if APP_PROPAGATE_DEBUG else False
    TESTING: TrueInDebug = None  # <- True if APP_PROPAGATE_DEBUG else False
    DEBUG_TEMPLATES: TrueInDebug = None  # <- True if APP_PROPAGATE_DEBUG else False
    DEBUG_RENDERED_TEMPLATES: TrueInDebug = None  # <- True if APP_PROPAGATE_DEBUG else False
    # this does'nt work (spend a day to find out), is SERVER_NAME: SERVER_ADDRESS = ""
    # https://flask.palletsprojects.com/en/latest/config/#SERVER_NAME
    # Inform the application what host and port it is bound to (NO Scheme).
    # SERVER_NAME = '' use it after understand how
    PREFERRED_URL_SCHEME = ""
    SECRET_KEY = ""
    SESSION_COOKIE_NAME = f"{APP_NAME.lower()}"

    """ SQLAlchemy
        --------------------------
    """
    SQLALCHEMY_DATABASE_URI = ""  # from os_environment
    SQLALCHEMY_DATABASE_URI_REMOVE_PW_REGEX = r":[^@]+@"
    SQLALCHEMY_DATABASE_URI_REPLACE_PW_STR = ":*******@"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    """ Log to file configuration
        --------------------------
    """
    LOG_TO_FILE = True  # Log
    LOG_MIN_LEVEL = logging.INFO
    # folder is log_files
    LOG_FILE_FOLDER = ""  # "log_files"
    LOG_FILE_NAME = ""  # defaults to APP_NAME.datetime.log
    LOG_FILE_STATUS = "?"  # internal set at startup

    """ Database constant
        --------------------------
    """
    # see canoa.vw_scm_sep
    SCM_SEP_SEPARATOR = "/"


# eof
