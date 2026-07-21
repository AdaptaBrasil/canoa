"""
SEP Log Grid
Read-only audit-log grid: shows a single SEP's history from `log_user_sep`
(see vw_log_user_sep / LogUserSepGrid). Reached from sep_grid's [Ver log] button.

Equipe da Canoa -- 2026
mgd 2026-07-16
"""

import json

from .UserSep import UserSep
from .sep_icon import do_icon_get_url
from ..public.ups_handler import get_ups_jHtml
from ..helpers.jinja_helper import Jinja_Rendered, process_template
from ..helpers.uiact_helper import UiActResponseProxy
from ..helpers.route_helper import get_private_response_data, init_response_vars, private_route
from ..helpers.js_consts_helper import JS_GRID_COL_META_INFO, js_ui_dictionary
from ..helpers.ui_db_texts_manager import UITextsKeys
from ..common.app_error_assistant import ModuleErrorCode
from ..models.private.sep import Sep
from ..models.private.mgmt_seps_user import MgmtSepsUser
from ..models.private.log_user_sep_grid import LogUserSepGrid


def get_sep_log_grid(sep_code: str) -> Jinja_Rendered:

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SEP_LOG_GRID)
    try:
        task_code += 1  # 1
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("sepLogGrid")

        task_code += 1  # 2
        sep_id = UserSep.to_id(sep_code)
        sep_row = Sep.get_row(sep_id)
        ui_db_texts[UITextsKeys.Form.icon_url] = do_icon_get_url(sep_row.icon_file_name if sep_row else "", sep_id)

        sep_info = MgmtSepsUser.get_seps_usr(["fullname"], sep_id=sep_id)
        sep_fullname = sep_info[0].fullname if len(sep_info) > 0 else sep_code
        ui_db_texts[UITextsKeys.Form.title] = ui_db_texts.format(UITextsKeys.Form.title, sep_fullname)

        task_code += 1  # 3
        col_names = ["curr_user_name", "prior_user_name", "operation", "done_by_name", "done_at"]
        js_ui_dict = js_ui_dictionary(ui_db_texts[JS_GRID_COL_META_INFO], col_names, task_code)

        task_code += 1  # 4
        log_data = LogUserSepGrid.get_rows(col_names, LogUserSepGrid.id_sep == sep_id)
        operation_labels = json.loads(ui_db_texts.get_str("jsonOperation", "{}"))
        ui_db_texts[UITextsKeys.Action.dlg_goto] = private_route("sep_grid", code=UiActResponseProxy.show)
        ui_db_texts[UITextsKeys.Action.dlg_sec_msg] = UiActResponseProxy.show

        for row in log_data:
            row.operation = operation_labels.get(row.operation, row.operation)
            row.done_at = row.done_at.isoformat()  # sortable string; sep_log_grid.js formats it for display

        task_code += 1  # 5
        jHtml = process_template(
            tmpl_ffn,
            log_data=log_data.to_list(),
            **ui_db_texts.data(),
            **js_ui_dict,
        )

    except Exception as e:
        jHtml = get_ups_jHtml("gridException", ui_db_texts, task_code, e)

    return jHtml


# eof
