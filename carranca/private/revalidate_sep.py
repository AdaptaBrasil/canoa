"""
Revalidate one SEP's stored file

Second layer of the "Validar Visíveis" feature (Refs #61):
runs a file, already stored, through `data_validate` again
(eg the validator or the SEP's spatial data was updated).

    - Service function, no request/template: sep_validate.py (POST) calls it
      with `ExportGrid.id` (the user_data_files.id of the SEP's last file).
    - The process runs as `app_user`, the user responsible for starting it:
      his folders, lock & `id_users`. Only the stored file is read from the sender's folder.
    - The report goes to the SEP's *current* manager (cc adm), or to adm when there is no manager.
    - Lock & folders cleanup mirror receive_file.py (TODO: share them).

Part of Canoa `File Validation` Processes (Revalidation)

Equipe da Canoa -- 09.2026
mgd
"""

# cSpell: ignore mgmt

import time
import shutil
from os import path, remove
from math import ceil
from typing import Tuple

from .UserSep import UserSep
from .validate_process.ProcessData import ProcessData
from .received_files.constants import FILE_ORIGIN_CLOUD
from .receive_file import RECEIVE_FILE_DEFAULT_ERROR
from ..models.public.user import User
from ..models.private.mgmt_seps_user import MgmtSepsUser
from ..models.private.user_data_files import UserDataFiles
from ..helpers.user_helper import UserFolders
from ..helpers.file_helper import ensure_folder_exists
from ..helpers.py_helper import is_str_none_or_empty
from ..common.app_context_vars import sidekick, app_user
from ..common.app_error_assistant import ModuleErrorCode
from ..config.ValidateProcessConfig import ValidateProcessConfig

# (error_code, msg_id, msg_arg): msg_id is a UI text key, msg_arg its argument
Revalidate_Result = Tuple[int, str, str]


class _Recipient:
    """report recipient, duck-typed as AppUser for rv_email"""

    def __init__(self, user: User):
        self.id = user.id
        self.name = user.username
        self.email = user.email


def _try_lock_process(pd: ProcessData) -> int:
    """
    Checks/acquires the processing lock of the user's folder.
    Returns 0 if acquired, the remaining minutes if locked, -1 on error.
    """
    lock_file = path.join(pd.path.data_tunnel_user_lock, pd.lock.file_name)
    if path.isfile(lock_file):
        age_minutes = (time.time() - path.getmtime(lock_file)) / 60
        if (remaining := pd.lock.ttl_min - age_minutes) > 0:
            return ceil(remaining)
        try:
            remove(lock_file)  # stale lock
        except OSError:
            pass

    try:
        open(lock_file, "x").close()
        return 0
    except FileExistsError:
        return pd.lock.ttl_min
    except Exception as e:
        sidekick.display.error(f"[revalidate_sep]: Lock process on folder [{lock_file}] failed: {e}.")
        return -1


def _cleanup_folders(proc: str, pd: ProcessData, rm_user_folders: bool, rm_lock_folder: bool) -> bool:
    def _rm(folder: str) -> bool:
        try:
            if path.isdir(folder):
                shutil.rmtree(folder)
            if path.isdir(folder):
                sidekick.display.fatal(f"[{proc}]: The intermediate process folder '{folder}' was not removed.")
                return False
            return True
        except Exception as e:
            sidekick.display.error(f"[{proc}]: The intermediate process folder {folder} was *not* removed due to an error: [{e}].")
            return False

    ok = _rm(pd.path.data_tunnel_user_lock) if rm_lock_folder else True
    if rm_user_folders:
        ok = _rm(pd.path.data_tunnel_user_write) and ok
        ok = _rm(pd.path.data_tunnel_user_read) and ok
    return ok


def revalidate_sep(udf_id: int) -> Revalidate_Result:
    """
    Revalidates the stored file of the user_data_files record `udf_id`.
    Runs synchronously (~1.5 min): one SEP per request.
    """
    # same as receive_file.py: Cargo imports receive_file
    from .validate_process.rv_process import rv_process

    proc = "revalidate_sep"
    error_code_base = ModuleErrorCode.SEP_VALIDATE.value
    task_code = 10
    pd: ProcessData | None = None
    lock_acquired = False
    remove_user_folders = True
    try:
        task_code += 1  # 11
        if not app_user.is_power:
            return error_code_base + task_code, "secKeyViolation", ""

        task_code += 1  # 12
        udf: UserDataFiles | None = UserDataFiles.get_row(udf_id) if udf_id > 0 else None
        if (
            udf is None
            or not udf.id_users
            or is_str_none_or_empty(udf.ticket)
            or is_str_none_or_empty(udf.file_name)
            or udf.file_size is None
            or udf.file_crc32 is None
        ):
            return error_code_base + task_code, "noRecord", str(udf_id)

        task_code += 1  # 13
        sep_row = MgmtSepsUser.get_sep_row(udf.id_sep) if udf.id_sep else None
        if sep_row is None:
            return error_code_base + task_code, "noRecord", str(udf.id_sep)
        sep_data = UserSep(**sep_row.copy([MgmtSepsUser.user_curr.name]))

        task_code += 1  # 14
        # the report goes to the SEP's current manager, None → adm (see rv_email.py)
        mgr_rows = MgmtSepsUser.get_seps_usr([MgmtSepsUser.user_id.name], None, udf.id_sep)
        mgr_id = mgr_rows[0].user_id if len(mgr_rows) > 0 else None
        mgr_user: User | None = User.get_row(mgr_id) if mgr_id else None
        report_recipient = None if mgr_user is None else _Recipient(mgr_user)
        if mgr_user is None:
            sidekick.display.warn(f"[{proc}]: SEP [{sep_data.fullname}] has no manager, the report goes to adm.")
        elif mgr_user.disabled:
            sidekick.display.warn(f"[{proc}]: The manager {mgr_user.username} of SEP [{sep_data.fullname}] is disabled.")

        task_code += 1  # 15
        cfg = ValidateProcessConfig(sidekick.debugging)
        remove_user_folders = cfg.remove_user_folders
        pd = ProcessData(
            app_user.code,
            app_user.folder,
            sidekick.config.COMMON_PATH,
            cfg.dv_app.folder,
            cfg.dv_app.batch,
            udf.file_origin == FILE_ORIGIN_CLOUD,
        )
        pd.received_file_name = udf.file_name.strip()
        pd.received_original_name = pd.received_file_name if is_str_none_or_empty(udf.original_name) else udf.original_name
        stored_file_name = f"{udf.ticket.strip()}_{pd.received_file_name}"  # as vw_base_data_files.stored_file_name
        src_full_name = UserFolders(udf.id_users).file_full_name(udf.file_origin, stored_file_name)

        task_code += 1  # 16
        if not ensure_folder_exists(pd.path.data_tunnel_user_lock):
            return error_code_base + task_code, RECEIVE_FILE_DEFAULT_ERROR, ""

        task_code += 1  # 17
        if (lock_result := _try_lock_process(pd)) > 0:
            return error_code_base + task_code, "receiveFileAdmit_wait", str(lock_result)
        elif lock_result < 0:
            return error_code_base + task_code, "receiveFileAdmit_bad_lock", ""
        lock_acquired = True

        task_code += 1  # 18
        if not _cleanup_folders("init", pd, True, False):
            return error_code_base + task_code, RECEIVE_FILE_DEFAULT_ERROR, ""

        task_code += 1  # 19
        sidekick.display.info(
            f"[{proc}]: {app_user.name} revalidates [{udf.ticket}] of SEP [{sep_data.fullname}]"
            + f", report to {'adm' if report_recipient is None else report_recipient.name}."
        )
        error_code, msg_id, _ = rv_process(
            app_user, report_recipient, sep_data, pd, src_full_name, udf.file_size, udf.file_crc32
        )
        if error_code == 0:
            return 0, "uploadFileSuccess", pd.user_receipt
        return error_code, msg_id, ""

    except Exception as e:
        sidekick.display.fatal(f"[{proc}]: Exception [{e}], code {error_code_base + task_code}, udf_id [{udf_id}].")
        return error_code_base + task_code, "receiveFileException", str(task_code)

    finally:
        # the lock belongs to another request unless acquired here
        if pd is not None and lock_acquired:
            _cleanup_folders("exit", pd, remove_user_folders, True)


# eof
