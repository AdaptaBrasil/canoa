"""
ValidateProcessConfig.py

Configuration for the validation process

(./private/validate_process)
Stores the configurable parameters required at each step

see README.md
Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024
mgd

"""

# cSpell:ignore

from typing import NamedTuple
from ..helpers.py_helper import OS_IS_WINDOWS, get_envvar
from ..helpers.email_helper import RecipientsDic


class OutputFile(NamedTuple):
    name: str
    ext: str


class DataValidateApp(NamedTuple):
    batch: str  # batch file name
    folder: str  # folder name
    ui_name: str  # the name of the app to display to user/log/etc
    flags: str  # flags for the app
    flag_debug: str  # debug flag
    # named arguments
    na_user_name: str  # user name argument
    na_file_name: str  # file name argument
    na_schema_se: str  # schema sector argument
    na_in_folder: str  # input folder argument
    na_out_folder: str  # output folder argument


class ValidateProcessConfig:
    _debug_process = None  # None -> set by param debug (see flag_debug)

    def __init__(self, debug=False):  #: BaseConfig
        # dv_app `data_validate` app output file name and extension
        self.output_file = OutputFile(name="data_report", ext=".pdf")
        self.dv_app = DataValidateApp(
            batch="run_validate."
            + ("bat" if OS_IS_WINDOWS else "sh"),  # TODO: OS_IS_LINUX
            folder="data_validate",  # ./<common_folder>/<folder>/python main.py
            ui_name="data_validate",  # user interface name
            flags="--no-spellchecker" if OS_IS_WINDOWS else "",  # any needed flags
            flag_debug="--debug",  # if self.debug_process is True, then use this flag
            # named argument
            na_schema_se="--sector",
            na_user_name="--user",
            na_file_name="--file",
            na_in_folder="--input_folder",
            na_out_folder="--output_folder",
        )
        _cc = get_envvar("EMAIL_REPORT_CC")
        self.cc_recipients = RecipientsDic(cc=_cc)  # reports's email cc recipients
        self.remove_tmp_files = True  # remove data_validate temporary files from (...data_tunnel/<user_code>/) used in the process [True]
        _debug = ValidateProcessConfig._debug_process  # hard coded debug flag
        self.debug_process = debug if _debug is None else bool(_debug)
        self.stdout_result_pattern = r"<\{\"data_validate\":.*?}>"


# eof
