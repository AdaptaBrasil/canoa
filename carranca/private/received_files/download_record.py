"""
User's Received Files's Management

    user request to download one of the files
    he has sent for validation or it's generated report.

Equipe da Canoa -- 2025
mgd 2025-01-14 03-18
"""

# cSpell: ignore samp rqst dnld rprt

import json
from os import path
from http import HTTPStatus
from flask import send_file, request, Response, abort

from .constants import DNLD_R, DNLD_F
from .fetch_records import fetch_record_s, IGNORE_USER, USER_RECEIPT
from ...helpers.py_helper import is_str_none_or_empty
from ...public.ups_handler import ups_handler
from ...helpers.file_helper import change_file_ext
from ...helpers.types_helper import UsualDict
from ...helpers.route_helper import MTD_GET, get_private_response_data, init_response_vars
from ...common.app_error_assistant import HTTPStatusCode, ModuleErrorCode, AppStumbled
from ...helpers.js_consts_helper import js_form_sec_check, js_form_cargo_id, js_grid_col_meta_info
from ...helpers.ui_db_texts_helper import add_msg_error


def download_rec() -> Response:
    task_code = ModuleErrorCode.RECEIVED_FILES_MGMT.value

    _, is_get, ui_db_texts = init_response_vars()

    file_response: Response = ""
    http_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    try:
        task_code += 1  # 1
        _, is_get, ui_db_texts = get_private_response_data("receivedFilesMgmt")

        def _raise(msg: str, hsc: int, log_out=False):
            nonlocal http_status_code
            http_status_code = hsc
            raise AppStumbled(msg, task_code, log_out, True)

        def _get_receipt(db_record: UsualDict):
            col_meta = ui_db_texts[js_grid_col_meta_info]
            caption = json.loads(col_meta)[USER_RECEIPT]
            return f"{caption}: [{db_record[USER_RECEIPT]}]."

        if is_get:
            msg = f"{add_msg_error(HTTPStatusCode.CODE_405.value, ui_db_texts)} (Requested: ${MTD_GET}.)"
            _raise(msg, HTTPStatus.METHOD_NOT_ALLOWED)

        task_code += 1  # 2
        rqst = request.form.get(js_form_cargo_id)
        rec_id, rec_type = rqst[:-1], rqst[-1]

        if not is_str_none_or_empty(msg_key := js_form_sec_check()):
            task_code += 1  # 3
            msg = add_msg_error(msg_key, ui_db_texts)
            _raise(msg, HTTPStatus.UNAUTHORIZED)
        elif not (rec_id.isdigit() and rec_type in [DNLD_R, DNLD_F]):
            task_code += 2  # 4
            msg = add_msg_error("secKeyViolation", ui_db_texts)
            _raise(msg, HTTPStatus.BAD_REQUEST, True)
        else:
            task_code += 3  # 5
            no_sep = ui_db_texts["itemNone"]
            db_records, download_file_name, report_ext = fetch_record_s(no_sep, rec_id, IGNORE_USER)
            if len(db_records) != 1:
                msg = add_msg_error("noRecord", ui_db_texts)
                _raise(msg, HTTPStatus.NOT_FOUND)

            if rec_type == DNLD_R:
                # This is a Report
                download_file_name = change_file_ext(download_file_name, report_ext)

            if path.isfile(download_file_name):
                file_response = send_file(download_file_name)
                http_status_code = HTTPStatus.OK
            else:  # deleted just now :-(
                msg = f"{add_msg_error("fileNotFound", ui_db_texts)} {_get_receipt(db_records[0])}"
                _raise(msg, HTTPStatus.GONE)

    except Exception as e:
        # ⚠️ Use default ups/error handler to log errors
        ups_handler(task_code, str(e), e)

        # ⚠️ Direct abort is required here
        # ---------------------------------
        abort(http_status_code, description=str(e))
        # ---------------------------------
        # This page runs during file download responses.
        #
        # Returning the project’s standard (`get_ups_jHtml` | 'ups_handler')
        # HTML error page would corrupt the binary stream and confuse the client.
        #
        # Future refactors/technical reviews: preserve this abort() call
        # unless the download mechanism itself is redesigned.
        # Do not use:
        # jHTML = get_ups_jHtml(http_status_code, ui_db_texts, task_code, e)
        # return jHTML

    return file_response


# eof
