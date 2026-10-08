"""
Revalidation, second step:
    - Link (or copy) the stored file under the new ticket name, so `unzip`, `submit`
      and the received files download find it like any other process.
    - Register the process in the user_data_files table (a new record).

    No file is received nor checked: `a_received_at` & `c_check_started_at` are kept NULL.

Part of Canoa `File Validation` Processes (Revalidation)

Equipe da Canoa -- 09.2026
mgd
"""

import shutil
from os import link, path, remove

from .Cargo import Next_Cargo, Cargo
from ...models.private.user_data_files import UserDataFiles
from ...helpers.py_helper import OS_IS_WINDOWS, now
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode
from ...private.received_files.constants import FILE_ORIGIN_CLOUD, FILE_ORIGIN_LOCAL


def _link_or_copy(src_full_name: str, work_fname: str) -> str:
    """hard link costs no disk space; copy when the file system can't link"""
    try:
        link(src_full_name, work_fname)
        return "linked"
    except FileExistsError:
        raise
    except OSError:
        shutil.copy2(src_full_name, work_fname)
        return "copied"


def rv_register(cargo: Cargo, src_full_name: str, file_size: int, file_crc32: int) -> Next_Cargo:
    error_code = 0
    task_code = 1
    msg_exception = ""
    file_saved = False
    file_registered = False
    work_fname = cargo.pd.working_file_full_name()
    proc = "[rv_register]: "
    try:
        task_code += 1  # 2
        register_started_at = now()
        if path.normcase(path.abspath(src_full_name)) == path.normcase(path.abspath(work_fname)):
            # never happens (new ticket), but `remove(work_fname)` below must never delete the source
            task_code += 1  # 3
            raise ValueError(f"The working file is the stored file [{src_full_name}].")

        task_code = 4  # 4
        how = _link_or_copy(src_full_name, work_fname)
        file_saved = True
        sidekick.display.info(f"{proc}The stored file was {how} as [{work_fname}].")

        task_code = 6  # 6
        user_dataFiles_key = cargo.pd.file_ticket
        UserDataFiles.insert(
            user_dataFiles_key,
            id_users=cargo.user.id,
            id_sep=cargo.sep_data.id,  # this is an FK
            id_spd=cargo.sep_data.spd_id,  # this is an FK, the SEP's current spatial data
            user_receipt=cargo.pd.user_receipt,
            app_version=cargo.app_version,
            process_version=cargo.process_version,
            # file info
            file_crc32=file_crc32,
            file_name=cargo.pd.received_file_name,
            file_origin=FILE_ORIGIN_LOCAL if cargo.pd.file_was_uploaded else FILE_ORIGIN_CLOUD,
            file_size=file_size,
            from_os="W" if OS_IS_WINDOWS else "L",  # Linux
            original_name=cargo.pd.received_original_name,
            # process times (a_received_at & c_check_started_at: never happened)
            b_process_started_at=cargo.process_started_at,
            d_register_started_at=register_started_at,
            log_file_name=sidekick.log_filename,
        )
        task_code += 1  # 7
        file_registered = cargo.file_registered(user_dataFiles_key)
        sidekick.display.info(f"{proc}The revalidation record was inserted into the table.")
    except Exception as e:
        error_code = ModuleErrorCode.RECEIVE_FILE_REGISTER.value + task_code
        msg_exception = str(e)
        msg_deleted = ""
        if file_saved and not file_registered:
            remove(work_fname)
            msg_deleted = " (so its working copy was deleted)"
        sidekick.display.fatal(f"{proc}Error registering the stored file [{src_full_name}]{msg_deleted}. Error: [{msg_exception}].")

    # goto module unzip
    return cargo.update(error_code, "", msg_exception, {}, {})


# eof
