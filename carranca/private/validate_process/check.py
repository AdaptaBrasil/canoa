"""
First step:
- Simple file validations
- Check if exist or create process folders

Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore werkzeug ext

from os import path

from ...common.app_context_vars import sidekick
from ...helpers.py_helper import is_str_none_or_empty, now
from ...helpers.db_helper import get_str_field_length
from ...helpers.file_helper import file_must_exist, folder_must_exist, is_same_file_name
from ...common.app_error_assistant import ModuleErrorCode

from ...models.private import UserDataFiles
from .Cargo import Cargo


def check(cargo: Cargo, file_data: object | str, valid_ext: list[str]) -> Cargo:
    error_code = 0
    msg_exception = ""
    task_code = 0
    cs = cargo.pd
    cargo.check_started_at = now()
    receive_method = "downloaded" if cs.file_was_downloaded else "uploaded"
    try:
        file_name_max_len = get_str_field_length(UserDataFiles, "file_name")

        if file_data is None:
            task_code = 1
        elif is_str_none_or_empty(cargo.user.email):
            task_code = 2
        elif is_str_none_or_empty(cs.received_file_name):
            task_code = 3
        elif is_str_none_or_empty(cargo.receive_file_cfg.output_file.name):
            task_code = 4
        elif is_str_none_or_empty(cargo.receive_file_cfg.output_file.ext):
            task_code = 5
        elif len(cs.received_file_name) > file_name_max_len:
            task_code = 7
        elif not any(cs.received_file_name.lower().endswith(ext.strip().lower()) for ext in valid_ext):
            task_code = 8
        # elif not response.headers.get('Content-Type') == ct in valid_content_types.split(',')): #check if really zip
        # task_code = 10
        elif not folder_must_exist(cs.path.working_folder):
            task_code = 11
        elif not folder_must_exist(cs.path.data_tunnel_user_read):
            task_code = 12
        elif not folder_must_exist(cs.path.data_tunnel_user_write):
            task_code = 13
        elif not path.isfile(cs.path.batch_source_name):
            task_code = 14
        elif not file_must_exist(
            cs.path.batch_full_name,
            cs.path.batch_source_name,
            True,
        ):
            task_code = 15
        else:
            task_code = 0

        if task_code == 0:
            if not is_same_file_name(cs.received_original_name, cs.received_file_name):
                sidekick.display.info(
                    f"The {receive_method} file [{cs.received_original_name}] has been renamed to [{cs.received_file_name}]."
                )
            sidekick.display.info(
                f"check: The {receive_method} file [{cs.received_file_name}] was successfully verified."
            )
        else:
            sidekick.display.error(
                f"The {receive_method} file [{cs.received_file_name}] failed in module `check` with code {task_code}."
            )

    except Exception as e:
        msg_exception = str(e)
        # is the highest possible (see ModuleErrorCode.RECEIVE_FILE_CHECK.value + 1)
        task_code = 19
        sidekick.display.fatal(
            f"Exception [{e}], code {task_code}, occurred in module `check` while validating the {receive_method} file [{cs.received_original_name}]."
        )

    # goto module register.py
    error_code = 0 if task_code == 0 else ModuleErrorCode.RECEIVE_FILE_CHECK.value + task_code
    return cargo.update(error_code, "", msg_exception, {"file_data": file_data})


# eof
