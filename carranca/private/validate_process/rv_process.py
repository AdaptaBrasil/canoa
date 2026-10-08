"""
Performs the revalidation process of a file already stored:
    1. rv_check:    verify that the stored file still has the same size & crc32; check infrastructure
    2. rv_register: link the stored file under a new ticket & save process info in DB.users_files
    3. Unzip:       unzip the stored file to the data_tunnel shared folder
    4. Spdata:      export the SEP's *current* spatial data for `data_validate`
    5. Submit:      send the unzipped files to `data_validate` and wait for the report
    6. rv_email:    send the validation report to the SEP's current manager (cc adm) or to adm

    Steps 3..5 are the same modules of process.py.
    The process runs as `app_user`, the user responsible for starting it (folders, lock, `id_users`),
    only the stored file (`src_full_name`) is in the folder of the user who sent it.
    The loop & final DB update mirror process.py (TODO: merge them, process(modules=...)).

Part of Canoa `File Validation` Processes (Revalidation)

Equipe da Canoa -- 09.2026
mgd
"""

# pyright: reportAttributeAccessIssue=false

from typing import Tuple

from ...models.private.user_data_files import UserDataFiles

from ..AppUser import AppUser
from ..UserSep import UserSep
from ...helpers.py_helper import is_str_none_or_empty, now
from ...common.app_error_assistant import ModuleErrorCode
from ...config.ValidateProcessConfig import ValidateProcessConfig

from .Cargo import Cargo
from .ProcessData import ProcessData

from .rv_check import rv_check
from .rv_register import rv_register
from .unzip import unzip
from .spdata import spdata
from .submit import submit
from .rv_email import rv_email

# process_version String(12): the `rv` prefix marks a revalidation record
RV_PROCESS_VERSION = "rv2026.09.16"


def rv_process(
    app_user: AppUser,
    report_recipient: object | None,
    sep_data: UserSep,
    proc_data: ProcessData,
    src_full_name: str,
    src_file_size: int,
    src_file_crc32: int,
) -> Tuple[int, str, str]:
    """
    `report_recipient`: the SEP's current manager (name, email) or None
    """
    from ...common.app_context_vars import sidekick

    current_module_name = __name__.split(".")[-1]

    def _get_next_params(cargo: Cargo) -> Tuple[Cargo, dict]:
        params = dict(cargo.next)
        return cargo.init(), params

    def _get_msg_exception(e: Exception, msg_exc: str, code: int) -> str:
        return f"rv_process: Exception: [{e}]; {current_module_name}.Exception: [{msg_exc}], Code [{code}]."

    def _log(msg):
        log = f"[rv_process]: {msg}"
        return log + ("" if log.endswith(".") else ".")

    def _updated(code):
        msg_ok = "The revalidation ended without error and t" if code == 0 else "T"
        msg_error = "" if code == 0 else f" although the revalidation ended with error_code= [{code}]"
        sidekick.display.info(_log(f"{msg_ok}he DB record was updated successfully{msg_error}."))
        return

    cargo = Cargo(
        RV_PROCESS_VERSION,
        sidekick.debugging,
        app_user,
        sep_data,
        ValidateProcessConfig(sidekick.debugging),
        proc_data,
        None,  # received_at: nothing is received
        {"src_full_name": src_full_name, "src_file_size": src_file_size, "src_file_crc32": src_file_crc32},
    )
    error_code = 0
    msg_error = ""
    msg_exception = ""
    elapsed_output = sidekick.display.set_elapsed_output(True)

    sidekick.display.info(_log(f"The revalidation process of [{src_full_name}] has begun"))

    for current_module in [rv_check, rv_register, unzip, spdata, submit, rv_email]:
        current_module_name = current_module.__name__
        try:
            cargo, next_module_params = _get_next_params(cargo)
            if current_module is rv_email:
                next_module_params["report_recipient"] = report_recipient
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

        process_ended = now()
        if is_str_none_or_empty(cargo.table_udf_key):
            # rv_check failures (eg crc32 mismatch) end here: no record, only the log
            sidekick.display.info(_log("No record was inserted"))
        elif error_code == 0:
            try:
                UserDataFiles.update(cargo.table_udf_key, error_code=0, success_text=msg_success, z_process_end_at=process_ended)
                _updated(0)
            except Exception as e:
                error_code = ModuleErrorCode.RECEIVE_FILE_PROCESS.value + 1
                sidekick.display.fatal(_log(f"An error occurred while updating the final revalidation record: [{e}]."))
        else:
            fatal_msg = f"Revalidating stored file [{cargo.pd.received_file_name}] raised error code {error_code} in module '{current_module_name}'."
            sidekick.display.fatal(_log(fatal_msg))
            try:
                UserDataFiles.update(
                    cargo.table_udf_key,
                    error_code=error_code,
                    success_text=msg_success,  # not really success but standard_output
                    e_unzip_started_at=cargo.unzip_started_at,
                    f_submit_started_at=cargo.submit_started_at,
                    g_report_ready_at=cargo.report_ready_at,
                    h_email_started_at=cargo.email_started_at,
                    z_process_end_at=process_ended,
                    error_msg=("<no error message>" if is_str_none_or_empty(msg_error) else msg_error),
                    error_text=msg_exception,
                )
                _updated(error_code)
            except Exception as e:
                error_code = ModuleErrorCode.RECEIVE_FILE_PROCESS.value + 2
                msg_exception = _get_msg_exception(e, msg_exception, error_code)
                sidekick.display.error(_log(msg_exception))

    except Exception as e:
        error_code = ModuleErrorCode.RECEIVE_FILE_PROCESS.value + 3
        msg_exception = _get_msg_exception(e, msg_exception, error_code)
        sidekick.display.fatal(_log(msg_exception))

    finally:
        sidekick.display.info(_log(f"The revalidation process end with error code [{error_code}]"))
        sidekick.display.set_elapsed_output(elapsed_output)

    return error_code, msg_error, msg_exception


# eof
