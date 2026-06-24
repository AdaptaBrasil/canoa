"""
Fourth step:
    Unzip the uploaded file to a common folder with `data_validate` app

Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore spddata
import json
import zipfile

from typing import Any, List, TypeAlias
from os import path

from .Cargo import Next_Cargo, Cargo
from ...helpers.py_helper import now
from ...models.private.spatial_data_file import SpatialDataFile
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode

Dict_Field_Values: TypeAlias = dict[str, list[int | str]]


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

    # goto module spddata.py
    # return cargo.update(error_code, msg_error, msg_exception)

    # ======================================================
    # TODO make its own module
    # mgd 2026.06.12 -- 16
    _module = "spddata"
    spd_file_name = ""
    spd_id = 0
    from ..spd_analysis import SPD_DATA_KEY_FIELDS, SPD_DATA_KEY_VALUES

    try:

        def _get_fields_dic(data_dic: dict[str, Any], fields: List[str]) -> dict[str, Dict_Field_Values]:
            fields_dic: dict[str, Dict_Field_Values] = {}
            if fields:
                fields_req: list[str] = [  # all fields that are in fields AND have values
                    field_name for field_name in fields if data_dic.get(SPD_DATA_KEY_FIELDS, {}).get(field_name, {}).get("has_values", False)
                ]
                field_values: dict[str, List[int | str]] = {  # fields: [values]
                    field_name: values for field_name, values in data_dic.get(SPD_DATA_KEY_VALUES, {}).items() if field_name in fields_req
                }
                fields_dic = {SPD_DATA_KEY_VALUES: field_values}
            return fields_dic

        task_code = 1
        export_type = cargo.receive_file_cfg.spd_data_export
        export_types = cargo.receive_file_cfg.SpdDataExport

        spd_id = -1 if export_type == export_types.NONE else cargo.sep_data.spd_id
        data_dic: Dict_Field_Values = {}

        if spd_id > 0 and (spd_data := SpatialDataFile.get_row(spd_id)) and (data_dic := json.loads(spd_data.file_data)):
            # we have data ;-)
            msg_error = "spd_extract_error"
            task_code += 1  # 2
            fields_dict = {}
            if export_type == export_types.FULL:
                task_code += 1  # 3
                fields_dict = {"_name": spd_data.spd_name, **data_dic}
            else:
                fields: List[str] = []
                match export_type:
                    case export_types.ATTRIBUTES:
                        task_code += 1  # 3
                        fields = list(data_dic.get(SPD_DATA_KEY_FIELDS, {}).keys())
                    case export_types.FIELDS:
                        task_code += 2  # 4
                        fields = [spd_data.field_id, spd_data.field_name, spd_data.field_alt_name]
                    case export_types.ID:
                        task_code += 3  # 6
                        fields = [spd_data.field_id]

                fields_dict = _get_fields_dic(data_dic, fields)
            if fields_dict:
                # {'values': {'id': [4355, 4381, 2241, 4364...}, '?': [?, ?...], ... }
                spd_name = spd_data.spd_name
                spd_file_name = f"{cargo.receive_file_cfg.spd_data_file.name}{cargo.receive_file_cfg.spd_data_file.ext}"
                spd_full_name = path.join(cargo.pd.path.data_tunnel_user_write, spd_file_name)
                task_code += 1  # 6
                data_str = json.dumps(fields_dict)
                with open(spd_full_name, "w", encoding="utf-8") as f:
                    f.write(data_str)

                sidekick.display.info(
                    f"[{_module}]: The related spatial data '{spd_name}' was saved as [{spd_file_name}] with {len(data_str):,} bytes."
                )
    except Exception as e:
        msg_exception = str(e)
        error_code = task_code + ModuleErrorCode.RECEIVE_FILE_GEODATA.value
        sidekick.display.fatal(f"[{_module}]: Error exporting spacial data id={spd_id}: [{e}].")

    # goto module submit.py
    return cargo.update(error_code, msg_error, msg_exception)


# eof
