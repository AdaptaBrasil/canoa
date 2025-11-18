# Equipe da Canoa -- 2024
#
# mgd
# cSpell:ignore ext
"""
Cargo is a class that helps to control
upload_file validation process loop.

Part of Canoa `File Validation` Processes
"""
from datetime import datetime
from typing import Optional

from ..receive_file import RECEIVE_FILE_DEFAULT_ERROR

from ..AppUser import AppUser
from ...helpers.py_helper import UsualDict, is_str_none_or_empty, now
from ...common.app_constants import APP_VERSION
from ...config.ValidateProcessConfig import ValidateProcessConfig

from ..UserSep import UserSep
from .ProcessData import ProcessData


class Cargo:
    name = "Cargo"
    default_error: str = RECEIVE_FILE_DEFAULT_ERROR

    def __init__(
        self,
        process_version: str,
        in_debug: bool,
        user: AppUser,
        sep_data: UserSep,
        receive_file_cfg: ValidateProcessConfig,
        process_data: ProcessData,
        received_at: datetime,
        first: dict,
    ):
        """
        Cargo is a class that assists the process loop.
        """
        self.init()
        self.in_debug_mode = in_debug
        self.user = user
        self.sep_data = sep_data
        self.receive_file_cfg = receive_file_cfg
        self.pd = process_data
        self.next = dict(first)

        self.step = 1
        self.final = {}  # the process.py return values
        self.app_version = APP_VERSION
        self.process_version = process_version
        """ Timestamp indicating when each process module begins its execution """
        self.received_at = received_at
        self.process_started_at = now()
        self.check_started_at = None
        self.unzip_started_at = None
        self.report_ready_at = None
        self.submit_started_at = None
        self.email_started_at = None
        """ same as file ticket, a unique key in table UserDataFiles """
        self.table_udf_key = None

    def file_registered(self, unique_key) -> bool:
        self.table_udf_key = unique_key
        return True

    def init(self):
        """initialization of the error variables and `next module parameters` (next) at each loop"""
        self.error_code = 0
        self.msg_error = ""
        self.msg_exception = ""
        self.next = {}
        return self

    def update(
        self,
        error_code: int,
        msg_error: str = "",
        msg_exception: str = "",
        next: Optional[dict] = {},
        final: Optional[UsualDict] = {},
    ) -> tuple[int, str, str, object]:
        """
        Updates the class with the 'next' procedure values

        Args:
            error_code (int):         error code (0 none)
            msg_error (str):          an entry in vw_ui_texts (see texts_helper.py[get_msg_error()])
            msg_exception (str):      exception error message, to be logged, in order to assist in the debugging process
            next (dict):              parameters for the `next` procedure
            final (dict):             collects items for the final result: `return final`

        Returns:
            tuple:
            int   error code (0 no error)
            str   an entry in vw_ui_texts (see texts_helper.py[get_msg_error()])
            str   exception error message, to be logged, in order to assist in the debugging process
            obj   self, the Cargo instance
        """
        self.step += 1
        self.error_code = error_code
        self.msg_error = Cargo.default_error if is_str_none_or_empty(msg_error) else msg_error
        self.msg_exception = msg_exception
        self.next = dict(next)  # new next procedure parameters
        self.final.update(final)  # keep data though loops
        # TODO self.elapsed.push(now())
        return (self.error_code, self.msg_error, self.msg_exception, self)


# eof
