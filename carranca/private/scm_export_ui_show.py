"""
Schema & Seps

A json containing the Schema table and its visible SEP is generated
to organize the information to submit to the DB.

mgd 2025.08
"""

from .sep_icon import do_icon_get_url
from .scm_data import scm_data_get
from ..helpers.py_helper import class_to_dict
from ..public.ups_handler import get_ups_jHtml
from ..helpers.types_helper import JinjaTemplate
from ..helpers.jinja_helper import process_template
from ..helpers.uiact_helper import UiActResponse, UiActResponseKeys
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.js_consts_helper import js_grid_col_meta_info, js_ui_dictionary
from ..config.ExportProcessConfig import ExportProcessConfig
from ..common.app_error_assistant import ModuleErrorCode
from ..models.private_1.ExportGrid import ExportGrid


def scm_export_ui_show(uiact_rsp: UiActResponse) -> JinjaTemplate:

    task_code = ModuleErrorCode.SCM_EXPORT_UI_SHOW
    jHtml, _, ui_db_texts = init_response_vars()

    try:
        task_code += 1
        tmpl_rfn, _, ui_db_texts = get_private_response_data("scmExportUiShow")

        task_code += 1
        scm_cols = ["name", "color"]
        sep_cols = ["name", "icon_file_name", "mgmt_users_id", "ui_order"]
        config = ExportProcessConfig(scm_cols, sep_cols)

        task_code += 1
        schema_data, task_code = scm_data_get(task_code, False, config)
        task_code += 1
        grid_data = ExportGrid.get_data()
        task_code += 1
        empty_icon = do_icon_get_url("")

        task_code += 1
        col_names = ["id", "sep_id", "scm_id", "file_name", "sep_fullname", "uploaded", "report_errors"]
        js_ui_dict = js_ui_dictionary(ui_db_texts[js_grid_col_meta_info], col_names, task_code)

        task_code += 1
        jHtml = process_template(
            tmpl_rfn,
            schemas=schema_data.schemas,
            grid_data=grid_data.to_list(),
            empty_icon=empty_icon,
            cargo_keys=class_to_dict(UiActResponseKeys),
            cargo=uiact_rsp.initial(),
            **ui_db_texts.dict(),
            **js_ui_dict,
        )
    except Exception as e:
        jHtml = get_ups_jHtml("scmExportException", ui_db_texts, task_code, e)

    return jHtml


# eof
