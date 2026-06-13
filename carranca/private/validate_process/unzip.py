"""
Third step:
- Unzip the uploaded file to a common folder with `data_validate` app

Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore spddata
import json
import zipfile
from os import path
from .Cargo import Next_Cargo, Cargo
from ...helpers.py_helper import now
from ...models.private.spatial_data_file import SpatialDataFile
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode


def unzip(cargo: Cargo) -> Next_Cargo:
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

        sidekick.display.info(f"[unzip]: The file was unpacked in [{unzip_folder}].")
    except Exception as e:
        msg_exception = str(e)
        error_code = task_code + ModuleErrorCode.RECEIVE_FILE_UNZIP.value
        sidekick.display.fatal(f"[unzip]: Error unzipping file [{zip_full_name}] in [{unzip_folder}]: [{e}].")

    # TODO make its own module
    # mgd 2026.06.12 -- 13
    _module = "spddata"
    spd_id = cargo.sep_data.spd_id
    if spd_id > 0:
        msg_error = "spd_extract_error"
        task_code += 1  # 5
        spd_file_name = f"{cargo.receive_file_cfg.spd_data_file.name}{cargo.receive_file_cfg.spd_data_file.ext}"
        spd_full_name = path.join(cargo.pd.path.data_tunnel_user_write, spd_file_name)
        try:
            task_code += 1  # 6
            spd_data = SpatialDataFile.get_row(spd_id)
            task_code += 1  # 7
            if spd_data:
                _data_dic = json.loads(spd_data.file_data)
                task_code += 1  # 8
                _data_json = {"_name": spd_data.spd_name, **_data_dic}
                task_code += 1  # 8
                _data_str = json.dumps(_data_json)
                _data_len = len(_data_str)
                with open(spd_full_name, "w", encoding="utf-8") as f:
                    f.write(_data_str)
                sidekick.display.info(f"[{_module}]: The related spatial data was saved as [{spd_file_name}], {_data_len} bytes.")
            else:
                sidekick.display.error(f"[{_module}]: No spatial data was found on record [{spd_id}].")
        except Exception as e:
            msg_exception = str(e)
            error_code = task_code + ModuleErrorCode.RECEIVE_FILE_UNZIP.value
            sidekick.display.fatal(f"[{_module}]: Error saving file [{spd_file_name}]: [{e}].")

    # goto module submit.py
    return cargo.update(error_code, msg_error, msg_exception)


# eof
