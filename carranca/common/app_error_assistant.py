"""
    *App Error Helpers*

    - Error Codes, per 'module'
    - Error Flags
    - Exception

Equipe da Canoa  2024 — 2025
mgd
"""

# type: ignore[reportUnknownMemberType]

from enum import IntEnum, StrEnum
from typing import Optional

from ..helpers.py_helper import crc16, now_as_iso


def proper_user_exception(e: Exception, task_code: int) -> str:
    """
    Handles exceptions by logging the error and returning an appropriate message
    based on the user's role.
    Args:
        e (Exception): The exception that occurred.
        task_code (int): A code representing the task during which the exception occurred.
    Returns:
        str: A detailed error message for support/administrative users, or a
             code (e-code) that is searchable in the log
    """
    from .app_context_vars import app_user, sidekick  # global_sidekick is not ready yet when this module is used

    error_str = str(e)
    code = crc16(error_str)
    info_str = f"e-code: {code}, task: {task_code}, date: {now_as_iso()}"

    sidekick.app_log.error(f"user: {app_user.id}, {info_str}, error: {error_str}")
    if app_user and app_user.ready and (app_user.is_support or app_user.is_adm):
        return error_str
    else:
        return info_str


def code_interrupted(e: Exception):
    """Is it me interrupted?"""
    return isinstance(e, JumpOut)


class JumpOut(Exception):
    """A specialized Exception to jump out from current route/code and give a message"""

    def __init__(self, msg: str, error_code: int = 0):
        self.msg = msg
        self.error_code = error_code


class AppStumbled(Exception):
    """A specialized Exception for Bug or Security Issue (logout)"""

    def __init__(
        self,
        msg: str,
        error_code: int = 0,
        logout: bool = False,
        is_fatal: bool = False,
        original_e: Optional[Exception] = None,
        tech_info: Optional[str] = None,
    ):
        self.msg = msg
        self.error_code = error_code
        self.logout = logout
        self.is_fatal = is_fatal
        self.original_e = original_e
        self.tech_info = tech_info

    def __str__(self):
        return f"{self.msg} (Error Code: {self.error_code}, Logout: {self.logout}, Fatal: {self.is_fatal})"


class ModuleErrorCode(IntEnum):
    # Public Access Control Processes
    ACCESS_CONTROL_LOGIN = 100  # 1-14
    ACCESS_CONTROL_REGISTER = 120  # 1-06
    ACCESS_CONTROL_PW_CHANGE = 130  # 1-08
    ACCESS_CONTROL_PW_RECOVERY = 140
    ACCESS_CONTROL_PW_RESET = 160

    # User Interface Text Retrieval
    UI_TEXTS = 170  # 1
    # Jinja Helper
    TEMPLATE_ERROR = 171
    TEMPLATE_BUG = 172

    # RECEIVE_FILE_* =: [200... 270] + 100
    RECEIVE_FILE_ADMIT = 200
    RECEIVE_FILE_CHECK = 210
    RECEIVE_FILE_REGISTER = 230
    RECEIVE_FILE_UNZIP = 240
    RECEIVE_FILE_SUBMIT = 250
    RECEIVE_FILE_EMAIL = 260
    RECEIVE_FILE_PROCESS = 270
    RECEIVE_FILE_EXCEPTION = 100  # this is added, as an exception, process.py

    NEXT_MODULE_ERROR = 400

    SEP_EDIT = 500
    SEP_MGMT = 550
    SEP_GRID = 600
    SCM_GRID = 700
    SCM_EDIT = 750
    SCM_EXPORT_UI_SHOW = 800
    SCM_EXPORT_UI_SAVE = 820
    SCM_EXPORT_DB = 840
    CONFIRM_EMAIL = 850

    DB_FETCH_ROWS = 590  # only on

    RECEIVED_FILES_MGMT = 700


class HTTPStatusCode(StrEnum):
    # this are key for table ui_items.name = <key>, section= 2 (secError)
    CODE_400 = "HTTP-400"  # 400 Bad Request:
    CODE_404 = "HTTP-404"  # 404 Not Found
    CODE_405 = "HTTP-405"  # 404 Not Found


class RaiseIf:
    """Flags to raise an error
    or just print the condition
    """

    ignite_no_sql_conn = True


# eof
