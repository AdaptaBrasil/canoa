"""
Performs the complete validation process:
    1. Check: file name, validates name, create folders
    2. Register: save process info( user, file, & times) in DB.users_files
    3. Unzip unzip the uploaded file
    4. Submit, sends the file to the `data_validate`
    5. Email, data_validate output is sent via email

    Cargo
        is a class to shares: ProcessData, Params, args, and return values between the 5 modules.

    ProcessData
        is a class that keep the files & folders names

    Params
        is as class that has the values of Configurable parameters of each module


Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore ext

from datetime import datetime
from typing import Tuple

from ...models.private import UserDataFiles

from ..AppUser import AppUser
from ..UserSep import UserSep
from ...helpers.py_helper import is_str_none_or_empty, now
from ...common.app_error_assistant import ModuleErrorCode
from ...config.ValidateProcessConfig import ValidateProcessConfig

from .Cargo import Cargo
from .ProcessData import ProcessData

from .check import check
from .unzip import unzip
from .email import email
from .submit import submit
from .register import register


def process(
    app_user: AppUser,
    sep_data: UserSep,
    file_data: object | str,
    proc_data: ProcessData,
    received_at: datetime,
    valid_ext: list[str],
) -> Tuple[int, str, str]:

    from ...common.app_context_vars import sidekick

    current_module_name = __name__.split(".")[-1]

    def _get_next_params(cargo: Cargo) -> Tuple[object, dict]:
        """
        Extracts the parameters of the next procedure,
        initialize cargo and returns to the loop
        """
        params = dict(cargo.next)
        return cargo.init(), params

    def _get_msg_exception(e: Exception, msg_exc: str, code: int) -> str:
        """prepares a complete exception message for the db & log"""
        return f"process: Exception: [{e}]; {current_module_name}.Exception: [{msg_exc}], Code [{code}]."

    def _display(msg):
        sidekick.display.info(f"process: {msg}.")
        return

    def _updated(code):
        msg_ok = "The process ended without error and t" if code == 0 else "T"
        msg_error = "" if code == 0 else f" although the process ended with error_code= [{code}]"
        _display(f"{msg_ok}he DB record was updated successfully{msg_error}")
        return

    # Create Cargo, with the parameters for the first procedure (check) of the Loop Process
    # "2025.02.05",  # process version, 22 new column user_files.sep_id
    cargo = Cargo(
        "2025.05.03",  # process version, user can have [0—n] sep.
        sidekick.debugging,
        app_user,
        sep_data,
        ValidateProcessConfig(sidekick.debugging),
        proc_data,
        received_at,
        {"file_data": file_data, "valid_ext": valid_ext},  # first module parameters
    )
    error_code = 0
    msg_error = ""
    msg_exception = ""
    elapsed_output = sidekick.display.set_elapsed_output(True)

    _display("The validation process has started")

    """
        Process Loop
        runs all the necessary steps (modules) to generate the final `report` and send it by email.

        `proc` Template:
        def proc(cargo: Cargo, param1, param2, ...) -> cargo:
          ''' process ....
    """
    for current_module in [check, register, unzip, submit, email]:
        current_module_name = current_module.__name__
        try:
            cargo, next_module_params = _get_next_params(cargo)
            error_code, msg_error, msg_exception, cargo = current_module(cargo, **next_module_params)
            if error_code > 0:
                break
        except Exception as e:
            error_code = (
                ModuleErrorCode.RECEIVE_FILE_PROCESS.value + cargo.step
                if error_code == 0
                else ModuleErrorCode.RECEIVE_FILE_EXCEPTION.value + error_code
            )
            msg_exception = _get_msg_exception(e, msg_exception, error_code)
            msg_error = cargo.default_error if is_str_none_or_empty(msg_error) else msg_error
            break

    try:
        if error_code == 0:
            current_module_name = "UserDataFiles.update"
        msg_success = cargo.final.get("msg_success", None)

        _display("Preparing to update the data validation process db record.")
        process_ended = now()
        if is_str_none_or_empty(cargo.table_udf_key):
            _display("No record was inserted")
        elif error_code == 0:
            try:
                UserDataFiles.update(
                    cargo.table_udf_key,
                    error_code=0,
                    success_text=msg_success,
                    z_process_end_at=process_ended,
                )
                _updated(0)
            except Exception as e:
                error_code = ModuleErrorCode.RECEIVE_FILE_PROCESS.value + 1
                fatal_msg = f"An error occurred while updating the final process record: [{e}]."
                sidekick.display.error(fatal_msg)
                sidekick.app_log.fatal(fatal_msg)
        else:
            fatal_msg = f"Processing {('downloaded' if cargo.pd.file_was_downloaded else 'uploaded')} file [{cargo.pd.received_file_name}] raised error code {error_code} in module '{current_module_name}'."
            sidekick.display.error(fatal_msg)
            sidekick.app_log.fatal(fatal_msg)
            try:
                UserDataFiles.update(
                    cargo.table_udf_key,
                    error_code=error_code,
                    success_text=msg_success,  # not really success but standard_output
                    # without error, this fields are saved in submit.py & email.py
                    e_unzip_started_at=cargo.unzip_started_at,
                    f_submit_started_at=cargo.submit_started_at,
                    g_report_ready_at=cargo.report_ready_at,
                    h_email_started_at=cargo.email_started_at,
                    z_process_end_at=process_ended,
                    error_msg=(
                        "<no error message>" if is_str_none_or_empty(msg_error) else msg_error
                    ),
                    error_text=msg_exception,
                )
                _updated(error_code)
            except Exception as e:
                error_code = ModuleErrorCode.RECEIVE_FILE_PROCESS.value + 2
                msg_exception = _get_msg_exception(e, msg_exception, error_code)
                sidekick.display.error(msg_exception)
                sidekick.app_log.fatal(msg_exception, exc_info=error_code)

    except Exception as e:
        error_code = ModuleErrorCode.RECEIVE_FILE_PROCESS.value + 3
        msg_exception = _get_msg_exception(e, msg_exception, error_code)
        sidekick.display.error(msg_exception)
        sidekick.app_log.fatal(msg_exception, exc_info=error_code)

    finally:
        _display(f"The validation process end with error code [{error_code}]")
        sidekick.display.set_elapsed_output(elapsed_output)

    return error_code, msg_error, msg_exception


# eof
