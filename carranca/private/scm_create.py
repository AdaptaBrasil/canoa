"""
Schema
Schema & Seps data create


mgd 2025.09
"""

# cSpell: ignore samp sepsusr usrlist

from ..public.ups_handler import ups_handler
from ..common.app_error_assistant import ModuleErrorCode, AppStumbled

from ..helpers.py_helper import class_to_dict
from ..helpers.uiact_helper import UiActResponseKeys
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import JinjaTemplate
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.js_consts_helper import js_grid_col_meta_info, js_ui_dictionary
from ..helpers.ui_db_texts_helper import add_msg_final
from ..helpers.db_records.DBRecords import ListOfDBRecords


def do_scm_create() -> JinjaTemplate:

    task_code = ModuleErrorCode.SCM_GRID.value
    tmpl, is_get, ui_texts = init_response_vars()
    scm_data: ListOfDBRecords = []

    try:
        task_code += 1  # 1
        tmpl_rfn, is_get, ui_texts = get_private_response_data("scmGrid")

        task_code += 1  # 3
        col_names = ["id", "name", "color", "visible", "sep_v2t"]
        js_ui_dict = js_ui_dictionary(ui_texts[js_grid_col_meta_info], col_names, task_code)

        scm_data = []
        if is_get:
            task_code += 1  # 4
            scm_data = _scm_data_fetch(col_names)
        else:
            raise AppStumbled("Unexpected route method.")

        tmpl = process_template(
            tmpl_rfn,
            scm_data=scm_data.to_list(),
            cargo_keys=class_to_dict(UiActResponseKeys),
            **ui_texts,
            **js_ui_dict,
        )

    except Exception as e:
        msg = add_msg_final("gridException", ui_texts, task_code)
        _, tmpl_rfn, ui_texts = ups_handler(task_code, msg, e)
        tmpl = process_template(tmpl_rfn, **ui_texts)

    return tmpl


# eof
