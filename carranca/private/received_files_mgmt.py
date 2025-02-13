"""
    User's Received Files's Management

    Equipe da Canoa -- 2025
    mgd 2025-01-14
"""

# cSpell: ignore mgmt tmpl samp

import json
from os import path
from flask import render_template

from ..helpers.pw_helper import internal_logout

from .models import ReceivedFiles
from ..common.app_context_vars import sidekick, logged_user
from ..config.config_validate_process import ValidateProcessConfig

from ..helpers.db_helper import ListOfRecords
from ..helpers.py_helper import is_str_none_or_empty
from ..helpers.user_helper import UserFolders
from ..helpers.file_helper import change_file_ext
from ..helpers.error_helper import ModuleErrorCode
from ..helpers.route_helper import get_private_form_data, init_form_vars
from ..helpers.hints_helper import UI_Texts
from ..helpers.ui_texts_helper import (
    add_msg_fatal,
    ui_msg_error,
    ui_msg_success,
    ui_msg_exception,
)


def received_files_fetch() -> ListOfRecords:

    user_id = None if logged_user is None else logged_user.id
    # todo user c//if user.

    received_files = ReceivedFiles.get_user_records(user_id)
    if received_files is None or len(received_files.records) == 0:
        return []
    else:
        files = 0
        uf = UserFolders()
        report_ext = ValidateProcessConfig(False).output_file.ext
        for record in received_files.records:
            folder = uf.uploaded if record.file_origin == "L" else uf.downloaded
            # create auxiliary fields
            record.file_full_name = path.join(folder, logged_user.folder, record.stored_file_name)
            record.file_found = path.isfile(record.file_full_name)
            record.report_found = path.isfile(change_file_ext(record.file_full_name, report_ext))
            if record.file_found:
                files += 1

    return received_files


def received_files_grid() -> str:

    task_code = ModuleErrorCode.RECEIVED_FILES_MGMT.value
    _, template, is_get, uiTexts = init_form_vars()

    users_sep: ListOfRecords = []
    sep_fullname_list = []

    try:
        task_code += 1  # 1
        template, is_get, uiTexts = get_private_form_data("receivedFilesMgmt")

        task_code += 1  # 2
        # TODO: create a real key with user_id and datetime
        js_grid_sec_value = "7298kaj0fk9dl-sd=)0y"
        # uiTexts keys used in JavaScript
        js_grid_sec_key = "gridSecKey"
        js_grid_rsp = "gridRsp"
        js_grid_submit_id = "gridSubmitID"

        # py/js communication
        uiTexts[js_grid_rsp] = js_grid_rsp
        uiTexts["gridSecValue"] = js_grid_sec_value
        uiTexts[js_grid_submit_id] = js_grid_submit_id
        uiTexts[js_grid_sec_key] = js_grid_sec_key

        task_code += 1  # 3
        colData = json.loads(uiTexts["colData"])
        task_code += 1  # 4
        # grid columns, colData & colNames *must* match in length.
        colNames = ["id", "file_name", "report_name", "submitted_at"]
        task_code += 1  # 5
        # Rewrite it in an easier way to express it in js: colName: colHeader
        uiTexts["colData"] = [{"n": key, "h": colData[key]} for key in colNames]

        def __get_grid_data():
            users_sep, sep_list, msg_error = MgmtUserSep.get_grid_view(uiTexts["itemNone"])
            sep_fullname_list = [sep["fullname"] for sep in sep_list]
            return users_sep, sep_fullname_list, msg_error

        if is_get:
            task_code += 1  # 6
            users_sep, sep_fullname_list, uiTexts[ui_msg_error] = __get_grid_data()
        elif request.form.get(js_grid_sec_key) != js_grid_sec_value:
            task_code += 2  # 7
            # TODO: create ann error page
            uiTexts[ui_msg_exception] = uiTexts["secKeyViolation"]
            internal_logout()
        else:
            task_code += 3
            txtGridResponse = request.form.get(js_grid_rsp)
            msg_success, msg_error, task_code = _save_and_email(txtGridResponse, uiTexts, task_code)
            task_code += 1
            users_sep, sep_fullname_list, msg_error_read = __get_grid_data()
            if is_str_none_or_empty(msg_error) and is_str_none_or_empty(msg_error_read):
                uiTexts[ui_msg_success] = msg_success
            elif is_str_none_or_empty(msg_error):
                uiTexts[ui_msg_error] = msg_error_read
            else:
                uiTexts[ui_msg_error] = msg_error

    except Exception as e:
        msg = add_msg_fatal("gridException", uiTexts, task_code)
        sidekick.app_log.error(e)
        sidekick.display.error(msg)
        # Todo error with users_sep,,, not ready

    tmpl = render_template(template, usersSep=users_sep, sepList=sep_fullname_list, **uiTexts)
    return tmpl


# eof
