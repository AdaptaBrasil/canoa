"""
SEP
Grid form Adm

mgd
"""

# cSpell: ignore samp sepsusr usrlist

from typing import List

from .sep_icon import do_icon_get_url
from ..models.private import MgmtSepsUser
from ..helpers.py_helper import class_to_dict
from ..public.ups_handler import get_ups_jHtml
from ..helpers.uiact_helper import UiActResponseKeys
from ..helpers.jinja_helper import JinjaGeneratedHtml, process_template
from ..helpers.route_helper import MTD_POST, get_private_response_data, init_response_vars
from ..helpers.js_consts_helper import js_grid_col_meta_info, js_ui_dictionary
from ..helpers.ui_db_texts_helper import add_msg_final
from ..common.app_error_assistant import ModuleErrorCode, AppStumbled, HTTPStatusCode
from ..helpers.db_records.DBRecords import DBRecords


def get_sep_grid() -> JinjaGeneratedHtml:

    def _sep_data_fetch(col_names: List[str]) -> DBRecords:
        sep_usr_rows = MgmtSepsUser.get_seps_usr(col_names)
        for record in sep_usr_rows:
            sep_id = record.id
            record.id = MgmtSepsUser.code(sep_id)
            record.icon_file_name = do_icon_get_url(record.icon_file_name, sep_id)

        return sep_usr_rows

    task_code = ModuleErrorCode.SEP_GRID.value
    jHtml, is_get, ui_db_texts = init_response_vars()

    try:
        task_code += 1  # 1
        tmpl_rfn, is_get, ui_db_texts = get_private_response_data("sepGrid")

        task_code += 1  # 2
        if not is_get:
            msg = f"{add_msg_final(HTTPStatusCode.CODE_405.value, ui_db_texts)} (Requested: ${MTD_POST}.)"
            raise AppStumbled(msg, task_code, False, True)

        task_code += 1  # 3
        col_names = ["id", "icon_file_name", "scm_name", "name", "user_curr", "visible"]
        js_ui_dict = js_ui_dictionary(ui_db_texts[js_grid_col_meta_info], col_names, task_code)

        task_code += 1  # 4
        sep_data = _sep_data_fetch(col_names)

        task_code += 1  # 5
        jHtml = process_template(
            tmpl_rfn,
            sep_data=sep_data.to_list(),
            cargo_keys=class_to_dict(UiActResponseKeys),
            **ui_db_texts.dict(),
            **js_ui_dict,
        )

    except Exception as e:
        jHtml = get_ups_jHtml("gridException", ui_db_texts, task_code, e)

    return jHtml


# eof
