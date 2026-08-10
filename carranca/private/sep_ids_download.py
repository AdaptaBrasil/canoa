"""
Download a SEP's spatial data ids as an .xlsx file (Refs #21)

    see
      carranca/private/spd_download.py

    menu
      "Setores Estratégicos" » Edição » [Baixar IDs]

Equipe da Canoa -- 2026
mgd 2026-08-04
"""

from io import BytesIO
from http import HTTPStatus
from flask import send_file, Response, abort, g
from openpyxl import Workbook
from werkzeug.utils import secure_filename

from .UserSep import UserSep
from .spd_analysis import get_id_values
from ..helpers.py_helper import is_str_none_or_empty
from ..models.private.sep import Sep
from ..public.ups_handler import ups_handler
from ..common.app_constants import APP_NAME
from ..helpers.route_helper import MTD_GET, get_private_response_data, init_response_vars
from ..common.app_constants import APP_RAW_HTTP_ERROR_RAISED
from ..common.app_context_vars import app_user
from ..helpers.js_consts_helper import js_form_sec_check
from ..common.app_error_assistant import HTTP_StatusCode, ModuleErrorCode, AppStumbled
from ..models.private.mgmt_seps_user import MgmtSepsUser
from ..models.private.spatial_data_file import SpatialDataFile


def download_ids(code: str) -> Response:

    _, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SEP_IDS_DOWNLOAD)

    file_response: Response = ""
    http_status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    try:
        task_code += 1  # 1
        _, is_get, ui_db_texts = get_private_response_data("sepGrid")

        def _raise(msg: str, hsc: int, log_out=False):
            nonlocal http_status_code
            http_status_code = hsc
            raise AppStumbled(msg, task_code, log_out, True)

        def _not_found(task_code: int):
            # same response for "doesn't exist" and "not yours" -- don't leak which one to a non-owner
            _, msg = ui_db_texts.set_msg_error(HTTP_StatusCode.CODE_404.value)
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
        elif (sep_id := UserSep.to_id(code)) < 1:
            _not_found(task_code + 3)
        elif not (sep_row := Sep.get_row(sep_id)):
            _not_found(task_code + 4)
        elif not app_user.is_power and sep_row.users_id != app_user.id:
            _not_found(task_code + 5)
        elif not sep_row.id_spd or not (spd_row := SpatialDataFile.get_row(sep_row.id_spd)):
            _not_found(task_code + 6)
        elif not (ids := get_id_values(spd_row)):
            _not_found(task_code + 7)
        else:
            task_code += 8
            sep_fullname = MgmtSepsUser.get_sep_row(sep_id).fullname
            updated_at = spd_row.edited_at if spd_row.edited_at is not None else spd_row.registered_at

            wb = Workbook()
            # Windows Explorer/Excel manage "Content created"/"Date last saved" on their own
            # terms regardless of what's set here -- fold the useful info into Comments instead.
            wb.properties.creator = APP_NAME
            wb.properties.title = f"IDs for SEP '{sep_row.name}'"
            wb.properties.subject = spd_row.spd_name
            wb.properties.description = f"IDs for: '{sep_fullname}', From Spatial File: '{spd_row.spd_name}', Count: {len(ids)}, Updated: '{updated_at:%Y/%m/%d %H:%M}'"

            ws = wb.active
            ws.title = spd_row.spd_name[:31]  # xlsx sheet name limit
            ws.append([spd_row.field_id])
            for value in ids:
                ws.append([value])

            buf = BytesIO()
            wb.save(buf)
            buf.seek(0)

            download_name = secure_filename(f"{sep_row.name}_{spd_row.field_id}.xlsx")
            file_response = send_file(
                buf,
                as_attachment=True,
                download_name=download_name,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            http_status_code = file_response.status_code

    except Exception as e:
        # ⚠️ Use default ups/error handler to log errors
        ups_handler(task_code, str(e), e)

        # g.<APP_RAW_HTTP_ERROR_RAISED>
        # ----------------
        # tells the app-wide error handlers (see carranca/__init__.py) to skip
        # their styled page and let Werkzeug render its plain default instead, since this
        # response is a file-download attempt, not a page navigation.
        setattr(g, APP_RAW_HTTP_ERROR_RAISED, True)

        # ⚠️ Direct abort is required here -- see spd_download.py for the full rationale
        # (an HTML error page here would corrupt the binary download stream)
        abort(http_status_code, description=str(e))

    return file_response


# eof
