"""
Download User Spatial Data Fiel

    see
      carranca/private/received_files/download_record.py

Equipe da Canoa -- 2026
mgd 2026-06-01
"""

# cSpell: ignore samp rqst dnld rprt

from os import path
from http import HTTPStatus
from flask import send_file, Response

from ..helpers.py_helper import is_str_none_or_empty
from ..helpers.route_helper import MTD_GET, get_private_response_data, init_response_vars
from ..common.abort_handler import abort_handler
from ..common.app_context_vars import sidekick
from ..helpers.js_consts_helper import js_form_sec_check
from ..common.app_error_assistant import HTTP_StatusCode, ModuleErrorCode, AppStumbled
from ..models.private.spatial_data_file import SpatialDataFile


def download_rec(code: str) -> Response:

    _, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SPD_DOWNLOAD)

    file_response: Response = ""
    http_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    _ofn = "original_file_name"
    _ufn = "file_name"
    try:
        task_code += 1  # 1
        _, is_get, ui_db_texts = get_private_response_data("spdGrid")

        def _raise(msg: str, hsc: int, log_out=False):
            nonlocal http_status_code
            http_status_code = hsc
            raise AppStumbled(msg, task_code, log_out, True)

        def _not_found(task_code: int):
            _, msg = ui_db_texts.set_msg_error("noRecord", task_code)
            _raise(msg, HTTPStatus.NOT_FOUND)
            return

        if is_get:
            task_code += 1
            _, msg_error = ui_db_texts.set_msg_error(HTTP_StatusCode.CODE_405.value)
            msg = f"{msg_error} (Requested: ${MTD_GET}.)"
            _raise(msg, HTTPStatus.METHOD_NOT_ALLOWED)
        elif not is_str_none_or_empty(msg_key := js_form_sec_check()):
            task_code += 2
            _, msg = ui_db_texts.set_msg_error(msg_key)
            _raise(msg, HTTPStatus.UNAUTHORIZED)
        elif (id := SpatialDataFile.to_id(code)) < 1:
            _not_found(task_code + 3)
        elif len(db_records := SpatialDataFile.get_rows(["id", "spd_name", _ufn, _ofn], id)) != 1:
            _not_found(task_code + 4)
        elif not (file_name := db_records[0][_ufn]):
            _not_found(task_code + 5)
        elif not (original_name := db_records[0][_ofn]):
            _not_found(task_code + 5)
        elif not path.isfile(ffn := path.join(sidekick.config.LOCAL_SPATIAL_DATA_PATH, file_name)):
            _not_found(task_code + 6)
        else:
            task_code += 7
            file_response = send_file(ffn, as_attachment=True, download_name=original_name)
            http_status_code = file_response.status_code

    except Exception as e:
        # see common.abort_handler for why this doesn't use the project's usual ups_handler page
        abort_handler(task_code, e, http_status_code)

    return file_response


# eof
