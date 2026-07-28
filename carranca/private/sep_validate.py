"""
SEP Validate Grid

Read-only grid: lists every currently-exportable SEP (visible, with real
submission history -- same `is_exportable` scope scm_export already uses),
showing who manages it, when it was last submitted and validated, which
validator version processed it, and the last result (errors/warnings).

First layer of the "Validar Visíveis" feature (Refs #61) -- display
only, no retest/email action yet.

Equipe da Canoa -- 2026
mgd 2026-07-28
"""

from ..config.FormIcons import FormIcons as fi
from ..public.ups_handler import get_ups_jHtml, ups_handler
from ..helpers.jinja_helper import Jinja_Rendered, process_template
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.js_consts_helper import JS_GRID_COL_META_INFO, js_ui_dictionary
from ..common.app_error_assistant import ModuleErrorCode
from ..models.private.ExportGrid import ExportGrid


def get_sep_validate_grid() -> Jinja_Rendered:

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SEP_VALIDATE)
    tmpl_ffn = ""
    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("sepValidate")

        if not is_get:
            # [Validar Todos] clicked -- retest/email logic (layer 2) still pending design
            # (background queue, process() invocation) -- same "under development" stub
            # already used for grid_route()'s `delete` action in routes.py.
            _, tmpl_ffn2, ui_texts = ups_handler(0, "A validação de todos os setores ainda está em desenvolvimento.")
            return process_template(tmpl_ffn2, **ui_texts)

        task_code += 1  # 2
        # display_cols: need a matching "colMetaInfo" (header) entry each -- see sepValidate DB text.
        # sep_id rides along in fetch_cols only, kept for the row-selection/retest layer, not shown.
        display_cols = ["sep_fullname", "manager_name", "uploaded_at", "validated_at", "validator_version", "report_errors", "report_warns"]
        fetch_cols = ["sep_id"] + display_cols
        js_ui_dict = js_ui_dictionary(ui_db_texts[JS_GRID_COL_META_INFO], display_cols, task_code)

        task_code += 1  # 3
        grid_data = ExportGrid.get_rows(fetch_cols, ExportGrid.is_exportable == True)

        task_code += 1  # 4
        jHtml = process_template(
            tmpl_ffn,
            grid_data=grid_data.to_list(),
            fi=fi.with_icon("sep_validate"),
            **ui_db_texts.data(),
            **js_ui_dict,
        )

    except Exception as e:
        jHtml = get_ups_jHtml("gridException", ui_db_texts, task_code, e)

    return jHtml


# eof
