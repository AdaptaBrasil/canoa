"""
SEP Validate Grid

Read-only grid: lists every currently-exportable SEP (visible, with real
submission history -- same `is_exportable` scope scm_export already uses),
showing who manages it, when it was last submitted and validated, which
validator version processed it, and the last result (errors/warnings).

First layer of the "Validar Visíveis" feature (Refs #61) -- display.
[Validar Um] wires the second layer: revalidates the selected row's stored
file (see `revalidate_file.py`) and redisplays the grid with the result.
[Validar Todos] (bulk, needs a background job) is still under development.

Equipe da Canoa -- 2026
mgd 2026-07-28
"""

from .. import global_dv_info
from .revalidate_file import revalidate_file
from ..config.FormIcons import FormIcons as fi
from ..helpers.py_helper import is_str_none_or_empty
from ..common.ups_handler import get_ups_jHtml, ups_handler
from ..helpers.jinja_helper import Jinja_Rendered, process_template, process_text
from ..helpers.route_helper import get_private_response_data, get_form_input_value, init_response_vars
from ..common.app_context_vars import sidekick
from ..helpers.js_consts_helper import JS_GRID_COL_META_INFO, js_form_sec_check, js_ui_dictionary
from ..helpers.ui_db_texts_manager import UITextsKeys
from ..models.private.ExportGrid import ExportGrid
from ..common.app_error_assistant import ModuleErrorCode


def get_sep_validate_grid() -> Jinja_Rendered:

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SEP_VALIDATE)
    tmpl_ffn = ""
    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("sepValidate")

        if not is_get and get_form_input_value("cmd") != "one":
            # [Validar Todos] (bulk, needs a background job) is still under development.
            _, tmpl_ffn2, ui_texts = ups_handler(0, "A validação de todos os setores ainda está em desenvolvimento.")
            return process_template(tmpl_ffn2, **ui_texts)

        task_code += 1  # 2
        if is_get:
            pass
        elif not is_str_none_or_empty(msg_error_key := js_form_sec_check()):
            task_code += 1  # 3
            ui_db_texts.set_msg_error(msg_error_key)
        else:
            task_code += 2  # 4
            code = ExportGrid.to_id(get_form_input_value("code"))
            error_code, msg_kind, msg_text = revalidate_file(code)
            ui_db_texts[msg_kind] = msg_text  # a compiled msg, from revalidate_file's own section
            if error_code > 0:
                # the "text below" of the error msg: the log file name, as receive_file.py
                ui_db_texts.set_value(UITextsKeys.Msg.tech, sidekick.log_filename)

        task_code += 1  # 3
        # display_cols: need a matching "colMetaInfo" (header) entry each -- see sepValidate DB text.
        # id/sep_id ride along in fetch_cols only, not shown as columns -- id (encoded via
        # to_code() below) for the [O Selecionado] POST (as udf_id), sep_id kept for later use.
        display_cols = ["sep_fullname", "manager_name", "uploaded_at", "validated_at", "validator_version", "report_errors", "report_warns"]
        fetch_cols = ["id", "sep_id"] + display_cols
        js_ui_dict = js_ui_dictionary(ui_db_texts[JS_GRID_COL_META_INFO], display_cols, task_code)

        task_code += 1  # 4
        # A row validated by another validator version than the current one is "old": only the difference
        # counts, no ordering (the formats, eg 0.7.64b677, are free-form). Without the current version
        # nothing is marked, a warning is shown and the buttons are disabled (template, js).
        dv_version = global_dv_info.version  # reading it may start a refresh (see DVInfo)
        dv_ready = global_dv_info.ready
        if not dv_ready and is_get:  # after a POST, the msg is the revalidation's
            ui_db_texts.set_msg_warn("validatorUnavailable")

        grid_data = ExportGrid.get_rows(fetch_cols, ExportGrid.is_exportable == True)
        for row in grid_data:
            # hidden column (not in display_cols): the grid colors the validator_version cell with it
            row.is_other_validator_version = dv_ready and row.validator_version != dv_version
            # don't ship the raw pk to the browser -- same obfuscation every other grid uses
            row.id = ExportGrid.to_code(row.id)
            # dates as local ISO for JS (Flask's tojson labels naive datetimes as GMT)
            row.uploaded_at = sidekick.to_iso_dt(row.uploaded_at)
            row.validated_at = sidekick.to_iso_dt(row.validated_at)

        task_code += 1  # 5
        # the validator's version follows the title: its own text, with Jinja ({{dv_version()}}), is rendered here
        title_validator = process_text(ui_db_texts.get_str("formTitleValidator")) if dv_ready else ""
        ui_db_texts.set_value(UITextsKeys.Form.title, f"{ui_db_texts.get_str(UITextsKeys.Form.title)} {title_validator}".strip())
        jHtml = process_template(
            tmpl_ffn,
            grid_data=grid_data.to_list(),
            dv_ready=dv_ready,
            fi=fi.with_icon("sep_validate"),
            **ui_db_texts.data(),
            **js_ui_dict,
        )

    except Exception as e:
        jHtml = get_ups_jHtml("gridException", ui_db_texts, task_code, e)

    return jHtml


# eof
