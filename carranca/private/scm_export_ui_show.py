"""
Schema & Seps

A json containing the Schema table and its visible SEP is generated
to organize the information to submit to the DB.

mgd 2025.08
"""

from .scm_data import get_scm_data
from .sep_icon import do_icon_get_url
from ..helpers.py_helper import class_to_dict
from ..public.ups_handler import get_ups_jHtml
from ..helpers.types_helper import Jinja_Template
from ..helpers.jinja_helper import process_template
from ..helpers.uiact_helper import UiActResponse, UiActResponseKeys
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.js_consts_helper import js_grid_col_meta_info, js_ui_dictionary
from ..models.private.ExportGrid import ExportGrid
from ..config.ExportProcessConfig import ExportProcessConfig
from ..common.app_error_assistant import ModuleErrorCode


def scm_export_ui_show(uiact_rsp: UiActResponse) -> Jinja_Template:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SCM_EXPORT_UI_SHOW)
    try:
        task_code += 1
        tmpl_ffn, _, ui_db_texts = get_private_response_data("scmExportUiShow")

        task_code += 1
        scm_cols = ["name", "color"]
        sep_cols = ["name", "icon_file_name", "mgmt_users_id", "ui_order"]
        config = ExportProcessConfig(False, scm_cols, sep_cols)

        task_code += 1
        schema_data, task_code = get_scm_data(task_code, config, False)
        task_code += 1  # 813
        grid_data = ExportGrid.get_rows()
        task_code += 1
        empty_icon = do_icon_get_url("")

        task_code += 1
        # TODO get names from table
        # col_names = [ExportGrid.id.name,...]
        col_names = ["id", "sep_id", "scm_id", "file_name", "sep_fullname", "uploaded", "report_errors"]
        js_ui_dict = js_ui_dictionary(ui_db_texts[js_grid_col_meta_info], col_names, task_code)

        task_code += 1
        jHtml = process_template(
            tmpl_ffn,
            schemas=schema_data.schemas,
            grid_data=grid_data.to_list(),
            empty_icon=empty_icon,
            cargo_keys=class_to_dict(UiActResponseKeys),
            cargo=uiact_rsp.initial(),
            **ui_db_texts.data(),
            **js_ui_dict,
        )
    except Exception as e:
        jHtml = get_ups_jHtml("uiExportException", ui_db_texts, task_code, e)

    return jHtml


# eof
