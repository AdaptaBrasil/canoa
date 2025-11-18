"""
Initialize the receive file process

Part of Canoa `File Validation` Processes
Equipe da Canoa -- 2024
mgd
"""

# cSpell: ignore werkzeug wtforms tmpl urlname uploadfile


from flask import request
from typing import TYPE_CHECKING, List
from werkzeug.utils import secure_filename


from ..public.ups_handler import ups_handler
from ..common.app_context_vars import sidekick, app_user
from ..common.app_error_assistant import ModuleErrorCode
from ..config.ValidateProcessConfig import ValidateProcessConfig

from .wtforms import ReceiveFileForm

from ..helpers.py_helper import (
    now,
    to_int,
    class_to_dict,
    is_str_none_or_empty,
)  # Ensure this module contains the function
from ..helpers.file_helper import folder_must_exist
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import JinjaTemplate
from ..helpers.route_helper import get_private_response_data, get_form_input_value
from ..helpers.dwnLd_goo_helper import is_gd_url_valid, download_public_google_file
from ..helpers.js_consts_helper import js_ui_dictionary
from ..helpers.ui_db_texts_helper import (
    UITextsKeys,
    add_msg_success,
    add_msg_error,
    add_msg_final,
)
from .validate_process.ProcessData import ProcessData

if TYPE_CHECKING:
    from .UserSep import UserSep, UserSepList, UserSepDict

RECEIVE_FILE_DEFAULT_ERROR: str = "uploadFileError"

# link em gd de test em mgd account https://drive.google.com/file/d/1yn1fAkCQ4Eg1dv0jeV73U6-KETUKVI58/view?usp=sharing


def _do_sep_placeholderOption(fullname: str) -> "UserSep":
    from .sep_icon import do_icon_get_url
    from .SepIconMaker import SepIconMaker
    from .UserSep import UserSep

    sep_fake = UserSep(-1, "", "", fullname, "", False, SepIconMaker.none_file, do_icon_get_url(""))  # empty
    return sep_fake


def receive_file() -> JinjaTemplate:
    tmpl_rfn, is_get, ui_db_texts = get_private_response_data("receiveFile")
    tmpl_form = ReceiveFileForm(request.form)

    # utils
    def _get_template(error_code) -> JinjaTemplate:
        seps: "UserSepList" = []
        ui_db_texts[UITextsKeys.Msg.tech] = ""
        ui_db_texts[UITextsKeys.Msg.info] = ""
        if error_code != 0:
            ui_db_texts[UITextsKeys.Msg.tech] = sidekick.log_filename
        elif not (seps := [sep for sep in app_user.seps]):
            ui_db_texts[UITextsKeys.Msg.warn] = ui_db_texts["noSEPassigned"]
            ui_db_texts[UITextsKeys.Msg.display_only_msg] = True
            seps: "UserSepList" = []
        elif len(seps) > 1:
            sep_placeholder_option = _do_sep_placeholderOption(ui_db_texts["placeholderOption"])
            seps.insert(0, sep_placeholder_option)

        ui_db_texts[UITextsKeys.Form.icon_url] = seps[0].icon_url if len(seps) > 0 else ""
        dict_seps: List[UserSepDict] = [class_to_dict(sep) for sep in seps]
        tmpl = process_template(tmpl_rfn, form=tmpl_form, seps=dict_seps, **ui_db_texts.dict(), **js_ui_dictionary())
        return tmpl

    def _log_error(msg_id: str, code: int, msg: str = "", fatal: bool = False) -> int:
        e_code = ModuleErrorCode.RECEIVE_FILE_ADMIT.value + code
        # AQUI BUG
        log_error = (
            add_msg_final(msg_id, ui_db_texts, e_code, msg)
            if fatal
            else add_msg_error(msg_id, ui_db_texts, e_code, msg)
        )
        sidekick.app_log.error(log_error)
        return e_code

    task_code = 1
    try:

        if is_get:
            return _get_template(0)

        received_at = now()
        # Find out what was kind of data was sent: an uploaded file or an URL (download)
        file_obj = request.files[tmpl_form.uploadfile.name] if len(request.files) > 0 else None
        task_code += 1  # 2
        url_str = get_form_input_value(tmpl_form.urlname.name)
        task_code += 1  # 3
        has_file = (file_obj is not None) and not is_str_none_or_empty(file_obj.filename)
        task_code += 1  # 4
        has_url = not is_str_none_or_empty(url_str)
        task_code += 1  # 5
        sep_id = to_int(get_form_input_value(tmpl_form.schema_sep.name))

        # file_data holds a 'str' or an 'obj'
        task_code += 1  # 6
        file_data = url_str if has_url else file_obj

        # get the select SEP

        # Basic check, both, none or bad url
        sep_data = next((sep for sep in app_user.seps if sep.id == sep_id), None)
        if sep_data is None:
            error_code = _log_error("receiveFileAdmit_bad_sep", task_code + 1, sep_id)  # 7
            return _get_template(error_code)
        elif has_file and has_url:
            error_code = _log_error("receiveFileAdmit_both", task_code + 2)  # 8
            return _get_template(error_code)
        elif not (has_file or has_url):
            error_code = _log_error("receiveFileAdmit_none", task_code + 3)  # 9
            return _get_template(error_code)
        elif has_url and is_gd_url_valid(url_str) > 0:
            error_code = _log_error("receiveFileAdmit_bad_url", task_code + 4)  # 10
            return _get_template(error_code)

        # Instantiate Process Data helper
        task_code = 13

        def doProcessData() -> tuple[bool, ProcessData]:
            receive_file_cfg = ValidateProcessConfig(sidekick.debugging)
            common_folder = sidekick.config.COMMON_PATH
            pd = ProcessData(
                app_user.code,
                app_user.folder,
                common_folder,
                receive_file_cfg.dv_app.folder,
                receive_file_cfg.dv_app.batch,
                has_url,
            )
            return receive_file_cfg.debug_process, pd

        task_code += 1  # 14
        debug_process, pd = doProcessData()
        if has_file:
            task_code += 1  # 15
            pd.received_original_name = file_obj.filename
            # TODO check file_obj. file_obj.mimetype file_obj.content_length
        elif not folder_must_exist(pd.path.working_folder):
            task_code += 2  # 16
            error_code = _log_error(RECEIVE_FILE_DEFAULT_ERROR, task_code)
            return _get_template(error_code)
        else:
            task_code += 3  # 17
            # {0} Placeholder for the actual file name.
            # Ensures pd.working_file_name() has the correct format.
            pd.received_file_name = "{0}"
            download_code, filename, md = download_public_google_file(
                url_str,
                pd.path.working_folder,
                pd.working_file_name(),
                True,
                debug_process,
            )
            if download_code == 0:
                task_code += 1  # 18
                pd.received_original_name = md["name"]
            else:
                sidekick.app_log.error(f"Download error code {download_code}.")
                fn = filename if filename else "<ainda sem nome>"
                task_code += 2  # 19
                error_code = _log_error("receiveFileAdmit_bad_dl", task_code, fn)
                return _get_template(error_code)

        pd.received_file_name = secure_filename(pd.received_original_name)
        task_code = 20  # 20
        ve = ui_db_texts["validExtensions"]
        valid_extensions = ".zip" if is_str_none_or_empty(ve) else ve.lower().split(",")

        task_code += 1  # 21
        from .validate_process.process import process

        task_code += 1  # 22
        error_code, msg_id, _ = process(app_user, sep_data, file_data, pd, received_at, valid_extensions)

        if error_code == 0:
            log_msg = add_msg_success("uploadFileSuccess", ui_db_texts, pd.user_receipt, app_user.email)
            sidekick.display.debug(log_msg)
        else:
            # keep error_code from process()
            _log_error(msg_id, task_code, "", True)

        tmpl = _get_template(error_code)
    except Exception as e:
        error_code = _log_error(RECEIVE_FILE_DEFAULT_ERROR, task_code + 1, "", True)
        sidekick.app_log.fatal(f"{RECEIVE_FILE_DEFAULT_ERROR}: Code {error_code}, Message: {e}.")
        msg = add_msg_final("receiveFileException", ui_db_texts, task_code)
        _, tmpl_rfn, ui_db_texts = ups_handler(task_code, msg, e)
        tmpl = process_template(tmpl_rfn, **ui_db_texts.dict())

    return tmpl


# eof
