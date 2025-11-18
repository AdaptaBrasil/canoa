"""
scm_export_layout

Saves the Schema & SEP User Interface layout

mgd 2025.08
"""

from typing import TypeAlias, Tuple, List

from ..helpers.py_helper import class_to_dict
from ..public.ups_handler import get_ups_jHtml
from ..helpers.uiact_helper import UiActResponseKeys, UiActResponse
from ..helpers.types_helper import JinjaTemplate
from ..helpers.jinja_helper import process_template
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.ui_db_texts_helper import add_msg_success
from ..common.app_error_assistant import ModuleErrorCode
from ..config.ExportProcessConfig import ExportProcessConfig

SepUiOrder: TypeAlias = List[Tuple[int, int]]


def scm_export_ui_save(uiact_rsp: UiActResponse) -> JinjaTemplate:
    from ..models.private import Sep

    task_code = ModuleErrorCode.SCM_EXPORT_UI_SAVE
    jHtml, _, ui_db_texts = init_response_vars()

    try:
        task_code += 1
        tmpl_rfn, _, ui_db_texts = get_private_response_data("scmExportUiSave")

        task_code += 1
        config = ExportProcessConfig()

        task_code += 1
        items: SepUiOrder = []

        task_code += 1
        current_scm_code = ""
        sep_new_index = 0
        for item in uiact_rsp.data["data"].split(","):
            scm_code, sep_code, _, _ = map(str, item.split(":"))
            if current_scm_code != scm_code:
                # Restart index at each Schema
                current_scm_code = scm_code
                sep_new_index = 0

            sep_new_index += 1
            # Decode obfuscated SEP code before saving
            sep_id: int = config.coder.decode(sep_code)
            items.append((sep_id, sep_new_index))

        task_code += 1
        Sep.save_ui_order(items, task_code)

        task_code += 1
        add_msg_success("saveSuccess", ui_db_texts)

        task_code += 1
        jHtml = process_template(tmpl_rfn, cargo_keys=class_to_dict(UiActResponseKeys), **ui_db_texts.dict())
    except Exception as e:
        jHtml = get_ups_jHtml("saveException", ui_db_texts, task_code, e)

    return jHtml


# eof
