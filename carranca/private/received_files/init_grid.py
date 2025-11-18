"""
User's Received Files's Management

Grid Initialization

Equipe da Canoa -- 2025
mgd 2025-01-14 & 03-18
"""

# cSpell: ignore samp rqst dnld rprt

from ...public.ups_handler import ups_handler, AppStumbled
from ...helpers.types_helper import JinjaTemplate
from ...helpers.jinja_helper import process_template
from ...helpers.route_helper import (
    get_private_response_data,
    init_response_vars,
    MTD_UNEXPECTED_ERROR,
)
from ...common.app_context_vars import app_user
from ...helpers.js_consts_helper import js_ui_dictionary
from ...helpers.ui_db_texts_helper import UITextsKeys, add_msg_final
from ...common.app_error_assistant import ModuleErrorCode

from .fetch_users import fetch_user_s
from .fetch_records import fetch_record_s, ALL_USER_RECS
from .constants import DNLD_F, DNLD_R


def init_grid(for_user: int) -> JinjaTemplate:

    task_code = ModuleErrorCode.RECEIVED_FILES_MGMT.value
    tmpl, _, ui_db_texts = init_response_vars()

    try:
        task_code += 1  # 1
        tmpl_rfn, is_get, ui_db_texts = get_private_response_data("receivedFilesMgmt")
        if not is_get:
            raise AppStumbled(MTD_UNEXPECTED_ERROR)
        task_code += 1  # 2
        if app_user.is_power:
            task_code += 1  # 3
            users = fetch_user_s()
            task_code += 1  # 4
            request_user = next((user for user in users if user.user_id == for_user), None)
            # TODO: if request_user is none Ups!
            task_code += 1  # 5
            users_list = [  # TODO: use user.code
                (  # id, name (files-count), enabled
                    str(user.user_id),
                    f"{user.user_name} ({user.files_count})",
                    user.user_name != request_user.user_name,
                )
                for user in users
            ]
            users_list.insert(
                0, ("", ui_db_texts[("noneUser" if len(users_list) == 0 else "selectUser")], True)
            )
            task_code += 1  # 6
            ui_db_texts[UITextsKeys.Form.title] = ui_db_texts[
                UITextsKeys.Form.title + "Power"
            ].format(request_user.user_name)
            user_id = request_user.user_id
        else:  # ignore `for_user`
            task_code += 4  # 6
            users_list = []
            user_id = app_user.id  # 2025.11.11 current_user.id

        # TODO check empty received_files
        task_code += 1  # 7
        file_recs, _, _ = fetch_record_s(ui_db_texts["itemNone"], ALL_USER_RECS, user_id)
        col_names = file_recs[0].keys() if file_recs else []
        task_code += 1  # 8
        js_ui_dict = js_ui_dictionary(ui_db_texts["colMetaInfo"], col_names, task_code)

        task_code += 1  # 9
        js_ui_dict["user_is_power"] = app_user.is_power
        js_ui_dict["dnld_F"] = DNLD_F  # Download File
        js_ui_dict["dnld_R"] = DNLD_R  # Download Report

        task_code += 1  # 10
        js_ui_dict["sel_id"] = "usr-list-id"
        task_code += 1  # 11 611
        tmpl = process_template(
            tmpl_rfn,
            files_rec=file_recs,
            users_list=users_list,
            **ui_db_texts.dict(),
            **js_ui_dict,
        )

    except Exception as e:
        msg = add_msg_final("gridException", ui_db_texts, task_code)
        _, tmpl_rfn, ui_db_texts = ups_handler(task_code, msg, e)
        tmpl = process_template(tmpl_rfn, **ui_db_texts.dict())

    return tmpl


# eof
