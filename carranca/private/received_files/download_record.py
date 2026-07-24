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
from flask import send_file, request, Response, abort, g

from .constants import DOWNLOAD_REPORT, DOWNLOAD_ZIPFILE
from .fetch_records import fetch_record_s, IGNORE_USER, USER_RECEIPT
from ...helpers.py_helper import is_str_none_or_empty, to_int
from ...public.ups_handler import ups_handler
from ...helpers.file_helper import change_file_ext
from ...helpers.types_helper import Usual_Dict
from ...helpers.route_helper import MTD_GET, get_private_response_data, init_response_vars
from ...common.app_error_assistant import HTTP_StatusCode, ModuleErrorCode, AppStumbled
from ...helpers.js_consts_helper import js_form_sec_check, JS_FORM_CARGO_ID, JS_GRID_COL_META_INFO


def download_rec() -> Response:

    _, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.RECEIVED_FILES_MGMT)

    file_response: Response = ""
    http_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    try:
        task_code += 1  # 1
        _, is_get, ui_db_texts = get_private_response_data("receivedFilesMgmt")

        def _raise(msg: str, hsc: int, log_out=False):
            nonlocal http_status_code
            http_status_code = hsc
            raise AppStumbled(msg, task_code, log_out, True)

        def _get_receipt(db_record: Usual_Dict):
            col_meta = ui_db_texts[JS_GRID_COL_META_INFO]
            caption = json.loads(col_meta)[USER_RECEIPT]
            return f"{caption}: [{db_record[USER_RECEIPT]}]."

        if is_get:
            _, msg_error = ui_db_texts.set_msg_error(HTTP_StatusCode.CODE_405.value)
            msg = f"{msg_error} (Requested: ${MTD_GET}.)"
            _raise(msg, HTTPStatus.METHOD_NOT_ALLOWED)

        task_code += 1  # 2
        rqst = request.form.get(JS_FORM_CARGO_ID)
        rec_id, rec_type = to_int(rqst[:-1]), rqst[-1]

        if not is_str_none_or_empty(msg_key := js_form_sec_check()):
            task_code += 1  # 3
            _, msg = ui_db_texts.set_msg_error(msg_key)
            _raise(msg, HTTPStatus.UNAUTHORIZED)
        elif not ((rec_id > 0) and rec_type in [DOWNLOAD_REPORT, DOWNLOAD_ZIPFILE]):
            task_code += 2  # 4
            _, msg = ui_db_texts.set_msg_error("secKeyViolation")
            _raise(msg, HTTPStatus.BAD_REQUEST, True)
        else:
            task_code += 3  # 5
            no_sep = ui_db_texts["itemNone"]
            db_records, download_file_name, uploaded_name, report_ext = fetch_record_s(no_sep, rec_id, IGNORE_USER)
            if len(db_records) != 1:
                _, msg = ui_db_texts.set_msg_error("noRecord")
                _raise(msg, HTTPStatus.NOT_FOUND)

            if rec_type == DOWNLOAD_REPORT:
                # This is a Report (PDF)
                download_file_name = change_file_ext(download_file_name, report_ext)
                uploaded_name = change_file_ext(uploaded_name, report_ext)

            if path.isfile(download_file_name):
                # TODO mimetype
                file_response = send_file(download_file_name, as_attachment=True, download_name=uploaded_name)
                http_status_code = HTTPStatus.OK
            else:  # deleted just now :-(
                _, msg_error = ui_db_texts.set_msg_error("fileNotFound")
                msg = f"{msg_error} {_get_receipt(db_records[0])}"
                _raise(msg, HTTPStatus.GONE)

    except Exception as e:
        # ⚠️ Use default ups/error handler to log errors
        ups_handler(task_code, str(e), e)

        # g.raw_http_error
        # ----------------
        # tells the app-wide error handlers (see carranca/__init__.py) to skip
        # their styled page and let Werkzeug render its plain default instead, since this
        # response is a file-download attempt, not a page navigation.
        # Note 2026-07-24
        g.raw_http_error = True

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
