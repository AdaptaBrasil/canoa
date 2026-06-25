"""
Fourth step:
    Export Spatial Data IDs and attributes to a JSON file for `data_validate`.
    Skipped when no spatial data file is associated with the current SEP.

Part of Canoa `File Validation` Processes

Equipe da Canoa --  06.2026
mgd
"""

# cSpell:ignore spddata

import json
from os import path
from typing import Any, List, TypeAlias

from .Cargo import Next_Cargo, Cargo
from ...models.private.spatial_data_file import SpatialDataFile
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode

Dict_Field_Values: TypeAlias = dict[str, list[int | str]]


def spddata(cargo: Cargo) -> Next_Cargo:
    """
    Writes a JSON file with the spatial data IDs and/or attributes
    to the data_tunnel write folder so `data_validate` can use them.
    Skipped when no spatial data is linked to the current SEP.
    """
    from ..spd_analysis import SPD_DATA_KEY_FIELDS, SPD_DATA_KEY_VALUES

    error_code = 0
    msg_error = ""
    msg_exception = ""
    task_code = 1
    spd_id = 0
    proc = "[spddata]: "

    try:

        def _get_fields_dic(data_dic: dict[str, Any], fields: List[str]) -> dict[str, Dict_Field_Values]:
            fields_req = [
                field_name for field_name in fields if data_dic.get(SPD_DATA_KEY_FIELDS, {}).get(field_name, {}).get("has_values", False)
            ]
            field_values = {
                field_name: values for field_name, values in data_dic.get(SPD_DATA_KEY_VALUES, {}).items() if field_name in fields_req
            }
            return {SPD_DATA_KEY_VALUES: field_values} if field_values else {}

        export_type = cargo.receive_file_cfg.spd_data_export
        export_types = cargo.receive_file_cfg.SpdDataExport

        spd_id = -1 if export_type == export_types.NONE else cargo.sep_data.spd_id
        data_dic: Dict_Field_Values = {}

        if spd_id > 0 and (spd_data := SpatialDataFile.get_row(spd_id)) and (data_dic := json.loads(spd_data.file_data)):
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
                        task_code += 3  # 5
                        fields = [spd_data.field_id]
                fields_dict = _get_fields_dic(data_dic, fields)

            if fields_dict:
                task_code += 1  # 6
                spd_file_name = f"{cargo.receive_file_cfg.spd_data_file.name}{cargo.receive_file_cfg.spd_data_file.ext}"
                spd_full_name = path.join(cargo.pd.path.data_tunnel_user_write, spd_file_name)
                data_str = json.dumps(fields_dict)
                with open(spd_full_name, "w", encoding="utf-8") as f:
                    f.write(data_str)
                sidekick.display.info(
                    f"{proc}The spatial data '{spd_data.spd_name}' was saved as [{spd_file_name}] with {len(data_str):,} bytes."
                )

    except Exception as e:
        msg_exception = str(e)
        error_code = task_code + ModuleErrorCode.RECEIVE_FILE_GEODATA.value
        sidekick.display.fatal(f"{proc}Error exporting spatial data id={spd_id}: [{e}].")

    # goto module submit.py
    return cargo.update(error_code, msg_error, msg_exception)


# eof
