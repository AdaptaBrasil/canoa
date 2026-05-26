"""
SPD
Spatial Data

Grid form Adm

mgd
"""

# cSpell: ignore samp sepsusr usrlist

from typing import List

from .wtforms import SpdEdit
from ..helpers.py_helper import class_to_dict
from ..public.ups_handler import get_ups_jHtml
from ..helpers.uiact_helper import UiActResponseKeys
from ..helpers.jinja_helper import Jinja_Rendered, process_template
from ..helpers.route_helper import MTD_POST, get_private_response_data, init_response_vars
from ..helpers.js_consts_helper import js_grid_col_meta_info, js_ui_dictionary
from ..helpers.ui_db_texts_manager import set_msg_fatal
from ..common.app_error_assistant import ModuleErrorCode, AppStumbled, HTTP_StatusCode
from ..helpers.db_records.DBRecords import DBRecords
from ..models.private.spatial_data_file import SpatialDataFile


def get_spd_grid() -> Jinja_Rendered:

    def _spd_data_fetch(col_names: List[str]) -> DBRecords:
        spd_usr_rows = SpatialDataFile.get_rows(col_names)
        for spd in spd_usr_rows:
            spd.id = SpatialDataFile.to_code(spd.id)
            spd.attributes = ", ".join(x for x in [spd.field_id, spd.field_name, spd.field_alt_name] if x)

        return spd_usr_rows

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SPD_GRID)
    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("spdGrid")

        task_code += 1  # 2
        if not is_get:
            msg = f"{set_msg_fatal(HTTP_StatusCode.CODE_405.value, ui_db_texts)} (Requested: ${MTD_POST}.)"
            raise AppStumbled(msg, task_code, False, True)

        task_code += 1  # 3

        base_col_names = ["id", "spd_name", "layer_name", "layer_crs", "layer_health", "features_count"]
        grid_col_names = base_col_names + ["attributes"]
        attributes_names = [f.name for f in SpdEdit().field_list]
        table_col_names = base_col_names + attributes_names

        js_ui_dict = js_ui_dictionary(ui_db_texts[js_grid_col_meta_info], grid_col_names, task_code)

        task_code += 1  # 4
        spd_rows = _spd_data_fetch(table_col_names).to_list()

        task_code += 1  # 5

        task_code += 1  # 6
        jHtml = process_template(
            tmpl_ffn,
            spd_rows=spd_rows,
            cargo_keys=class_to_dict(UiActResponseKeys),
            **ui_db_texts.data(),
            **js_ui_dict,
        )

    except Exception as e:
        jHtml = get_ups_jHtml("gridException", ui_db_texts, task_code, e)

    return jHtml


# eof
