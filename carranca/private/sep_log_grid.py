"""
SEP Log Grid
Read-only audit-log grid: shows a single SEP's history from `log_user_sep`
(see vw_log_user_sep / LogUserSepGrid). Reached from sep_grid's and sep_mgmt's
[Ver log] buttons -- ?from= tells [Voltar] which one to return to.

Equipe da Canoa -- 2026
mgd 2026-07-16
"""

import json

from .UserSep import UserSep
from .sep_icon import do_icon_get_url
from ..common.ups_handler import get_ups_jHtml
from ..helpers.jinja_helper import Jinja_Rendered, process_template
from ..helpers.uiact_helper import UiActResponseProxy
from ..helpers.route_helper import get_private_response_data, init_response_vars, private_route
from ..common.app_context_vars import app_user
from ..helpers.js_consts_helper import JS_GRID_COL_META_INFO, js_ui_dictionary
from ..helpers.ui_db_texts_manager import UITextsKeys
from ..common.app_error_assistant import ModuleErrorCode, JumpOut
from ..models.private.sep import Sep
from ..models.private.mgmt_seps_user import MgmtSepsUser
from ..models.private.log_user_sep_grid import LogUserSepGrid


def get_sep_log_grid(sep_code: str, from_page: str = "sep_grid") -> Jinja_Rendered:

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SEP_LOG_GRID)
    tmpl_ffn = ""
    try:
        task_code += 1  # 1
        tmpl_ffn, _, ui_db_texts = get_private_response_data("sepLogGrid")

        task_code += 1  # 2
        sep_id = UserSep.to_id(sep_code)
        sep_row = Sep.get_row(sep_id)

        sep_info = MgmtSepsUser.get_seps_usr(["fullname"], sep_id=sep_id)
        sep_fullname = sep_info[0].fullname if len(sep_info) > 0 else sep_code
        ui_db_texts[UITextsKeys.Form.title] = ui_db_texts.format(UITextsKeys.Form.title, sep_fullname)

        if not sep_row:
            task_code += 1  # 3
            _, msg_fatal = ui_db_texts.set_msg_fatal("sepLogNotFound")
            raise JumpOut(msg_fatal, task_code)
        elif not app_user.is_power and sep_row.users_id != app_user.id:
            task_code += 2  # 4
            _, msg_fatal = ui_db_texts.set_msg_fatal("sepLogNotAllowed", sep_fullname)
            raise JumpOut(msg_fatal, task_code)

        ui_db_texts[UITextsKeys.Form.icon_url] = do_icon_get_url(sep_row.icon_file_name, sep_id)

        task_code += 3  # 5
        col_names = ["curr_user_name", "prior_user_name", "operation", "done_by_name", "done_at"]
        js_ui_dict = js_ui_dictionary(ui_db_texts[JS_GRID_COL_META_INFO], col_names, task_code)

        task_code += 1  # 6
        log_data = LogUserSepGrid.get_rows(col_names, LogUserSepGrid.id_sep == sep_id)
        operation_labels = json.loads(ui_db_texts.get_str("jsonOperation", "{}"))
        # from_page is user-supplied (?from=), whitelist it -- sep_mgmt's route takes no `code`, unlike sep_grid's
        goto_url = private_route("sep_mgmt") if from_page == "sep_mgmt" else private_route("sep_grid", code=UiActResponseProxy.show)
        ui_db_texts[UITextsKeys.Action.dlg_goto] = goto_url
        ui_db_texts[UITextsKeys.Action.dlg_sec_msg] = UiActResponseProxy.show

        for row in log_data:
            row.operation = operation_labels.get(row.operation, row.operation)
            row.done_at = row.done_at.isoformat()  # sortable string; sep_log_grid.js formats it for display

        task_code += 1  # 7
        jHtml = process_template(
            tmpl_ffn,
            log_data=log_data.to_list(),
            **ui_db_texts.data(),
            **js_ui_dict,
        )

    except JumpOut:
        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("gridException", ui_db_texts, task_code, e)

    return jHtml


# eof
