"""
Third step:
- Unzip the uploaded file to a common folder with `data_validate` app

Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore

import zipfile
from .Cargo import Cargo
from ...helpers.py_helper import now
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode


def unzip(cargo: Cargo) -> Cargo:
    """
    Check the uploaded file as a zip,
    unzip it into the data_tunnel shared folder
    with `data_validate` app
    """

    msg_error = ""
    error_code = 0
    msg_exception = ""
    task_code = 1

    cargo.unzip_started_at = now()
    zip_full_name = cargo.pd.working_file_full_name()
    unzip_folder = cargo.pd.path.data_tunnel_user_write

    try:
        task_code += 1  # 2
        msg_error = "uploadFileZip_unknown"
        with zipfile.ZipFile(zip_full_name, "r") as zip_file:
            if zip_file.testzip() is not None:
                task_code += 1  # 3
                msg_error = "uploadFileZip_corrupted"
                raise RuntimeError(msg_error)
            else:
                task_code += 2  # 4
                msg_error = "uploadFileZip_extraction_error"
                zip_file.extractall(unzip_folder)
                msg_error = ""

        sidekick.display.info(f"unzip: The file was unpacked in [{unzip_folder}].")
    except Exception as e:
        msg_exception = str(e)
        error_code = task_code + ModuleErrorCode.RECEIVE_FILE_UNZIP.value
        sidekick.display.fatal(
            f"Error unzipping file [{zip_full_name}] in [{unzip_folder}]: [{e}].", exc_info=error_code
        )

    # goto module submit.py
    return cargo.update(error_code, msg_error, msg_exception)


# eof
