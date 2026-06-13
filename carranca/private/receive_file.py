"""
Initialize the receive file process

Part of Canoa `File Validation` Processes
Equipe da Canoa -- 2024
mgd
"""

# cSpell: ignore werkzeug wtforms tmpl urlname upload_file

from flask import request
from typing import TYPE_CHECKING, Any, List, Tuple
from werkzeug.utils import secure_filename


from .wtforms import ReceiveFileForm
from ..common.Display import Display
from ..common.UIDBTexts import UIDBTexts
from ..config.FormIcons import FormIcons as fi
from ..public.ups_handler import ups_handler
from ..common.app_context_vars import sidekick, app_user
from ..common.app_error_assistant import ModuleErrorCode
from ..config.ValidateProcessConfig import ValidateProcessConfig


from ..helpers.py_helper import now, is_str_none_or_empty
from ..helpers.file_helper import folder_must_exist
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import Jinja_Template, Usual_Dict, Jinja_Rendered
from ..helpers.route_helper import get_private_response_data, get_form_input_value, init_response_vars
from ..helpers.dwnLd_goo_helper import is_gd_url_valid, download_public_google_file
from ..helpers.js_consts_helper import js_ui_dictionary
from .validate_process.ProcessData import ProcessData
from ..models.private.spatial_data_file import SpatialDataFile
from ..helpers.ui_db_texts_manager import (
    UITextsKeys,
    set_msg_success,
    set_msg_error,
    set_msg_fatal,
    set_msg_warn,
)

if TYPE_CHECKING:
    from .UserSep import UserSep, UserSepList

RECEIVE_FILE_DEFAULT_ERROR: str = "uploadFileError"

# link em gd de test em mgd account https://drive.google.com/file/d/1yn1fAkCQ4Eg1dv0jeV73U6-KETUKVI58/view?usp=sharing


def _do_sep_placeholderOption(fullname: str) -> "UserSep":
    from .sep_icon import do_icon_get_url
    from .SepIconMaker import SepIconMaker
    from .UserSep import UserSep

    id_fake = -1
    name_fake = ""
    sep_fake = UserSep(
        id_fake, name_fake, id_fake, name_fake, name_fake, fullname, "", False, SepIconMaker.none_file, do_icon_get_url("")
    )  # empty
    return sep_fake


def receive_file() -> Jinja_Template:
    # Leave it here, unless you know why you need to change it.
    from .validate_process.process import process

    # utils
    def _get_template(ui_db_texts: UIDBTexts, error_code: int) -> Jinja_Rendered:
        # UPDATE ui_db_texts
        seps: "UserSepList" = []
        ui_db_texts.reset_messages()
        # mew ui_db_texts ui_db_texts[UITextsKeys.Msg.tech] = ""
        # ui_db_texts[UITextsKeys.Msg.info] = ""
        if error_code != 0:
            ui_db_texts.set_value(UITextsKeys.Msg.tech, sidekick.log_filename)
        elif not (seps := [sep for sep in app_user.seps]):
            ui_db_texts.set_msg_warn("noSEPassigned")
            seps: "UserSepList" = []
        elif len(seps) > 1:
            sep_placeholder_option = _do_sep_placeholderOption(ui_db_texts.get_str("placeholderOption"))
            seps.insert(0, sep_placeholder_option)

        ui_db_texts.set_value(UITextsKeys.Form.icon_url, seps[0].icon_url if len(seps) > 0 else "")
        seps_list: List[Usual_Dict] = [{"code": sep.code, "fullname": sep.fullname, "icon_url": sep.icon_url} for sep in seps]
        tmpl = process_template(tmpl_ffn, form=fform, seps=seps_list, fi=fi.with_icon(), **ui_db_texts.data(), **js_ui_dictionary())
        return tmpl

    def _log_issue(ui_db_texts: UIDBTexts, msg_type: Display.Kind, error_code: int, msg_id: str, task_code: int, msg_arg: str = "") -> int:
        local_error = ModuleErrorCode.RECEIVE_FILE_ADMIT.value + task_code
        show_code = f"{local_error}" if error_code == 0 else f"{error_code}:{task_code}"
        # UPDATE ui_db_texts
        match msg_type:
            case Display.Kind.WARN:
                msg_arg = set_msg_warn(msg_id, ui_db_texts, show_code, msg_arg)
            case Display.Kind.ERROR:
                msg_arg = set_msg_error(msg_id, ui_db_texts, show_code, msg_arg)
            case Display.Kind.FATAL:
                msg_arg = set_msg_fatal(msg_id, ui_db_texts, show_code, msg_arg)

        sidekick.display.type(msg_type, msg_arg)
        return local_error

    # def _update_sep_data( sep_data : UserSep):
    #     # TODO: SEP_DATA Temporary: until the view MgmtSepsUser is updated
    #     # MgmtSepsUser
    #     # spd_id = Column(Integer)
    #     # spd_name = Column(String(100))
    #     # spd_file = Column(String(100))

    #     spd_id = sep_data.id
    #     sep_row = Sep
    #     spd_row: SpatialDataFile = SpatialDataFile.get_row(spd_id)
    #                 spd_row.file_name = ufn
    #         spd_row.file_crc32 = file_crc32

    jHtml, is_get, ui_texts, task_code = init_response_vars(ModuleErrorCode.LEGACY_STYLE)
    fform = ReceiveFileForm()

    try:
        tmpl_ffn, is_get, ui_texts = get_private_response_data("receiveFile")

        if is_get:
            return _get_template(ui_texts, 0)

        received_at = now()
        # Find out what was kind of data was sent: an uploaded file or an URL (download)
        file_obj: Any = request.files[fform.upload_file.name] if len(request.files) > 0 else None
        task_code += 1  # 2
        url_str = get_form_input_value(fform.urlname.name)
        task_code += 1  # 3
        has_file = (file_obj is not None) and not is_str_none_or_empty(file_obj.filename)
        task_code += 1  # 4
        has_url = not is_str_none_or_empty(url_str)
        task_code += 1  # 5
        sep_code = get_form_input_value(fform.schema_sep.name)

        # file_data holds a 'str' or an 'obj'
        task_code += 1  # 6
        file_data = url_str if has_url else file_obj

        # get the select SEP

        # Basic file origin check: both, none or bad url
        sep_data = next((sep for sep in app_user.seps if sep.code == sep_code), None)
        if sep_data is None:
            _log_issue(ui_texts, Display.Kind.WARN, 0, "receiveFileAdmit_bad_sep", task_code + 1, sep_code)  # 7
            return _get_template(ui_texts, 0)
        elif has_file and has_url:
            _log_issue(ui_texts, Display.Kind.WARN, 0, "receiveFileAdmit_both", task_code + 2)  # 8
            return _get_template(ui_texts, 0)
        elif not (has_file or has_url):
            _log_issue(ui_texts, Display.Kind.WARN, 0, "receiveFileAdmit_none", task_code + 3)  # 9
            return _get_template(ui_texts, 0)
        elif has_url and is_gd_url_valid(url_str) > 0:
            _log_issue(ui_texts, Display.Kind.WARN, 0, "receiveFileAdmit_bad_url", task_code + 4)  # 10
            return _get_template(ui_texts, 0)

        # Instantiate Process Data helper
        task_code = 13

        def doProcessData() -> Tuple[bool, ProcessData]:
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
            error_code = _log_issue(ui_texts, Display.Kind.ERROR, 0, RECEIVE_FILE_DEFAULT_ERROR, task_code)
            return _get_template(ui_texts, error_code)
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
                sidekick.display.error(f"Download error code {download_code}.")
                fn = filename if filename else "<ainda sem nome>"
                task_code += 2  # 19
                error_code = _log_issue(ui_texts, Display.Kind.ERROR, 0, "receiveFileAdmit_bad_dl", task_code, fn)
                return _get_template(ui_texts, error_code)

        pd.received_file_name = secure_filename(pd.received_original_name)
        task_code = 20  # 20
        ve = ui_texts["validExtensions"]
        valid_extensions = [".zip"] if is_str_none_or_empty(ve) else ve.lower().split(",")

        task_code += 1  # 21
        # TODO: SEP_DATA
        ## _update_sep_data(sep_data)

        task_code += 1  # 21

        error_code, msg_id, _ = process(app_user, sep_data, file_data, pd, received_at, valid_extensions)

        if error_code == 0:
            log_msg = set_msg_success("uploadFileSuccess", ui_texts, pd.user_receipt, app_user.email)
            sidekick.display.debug(log_msg)
        else:
            _log_issue(ui_texts, Display.Kind.FATAL, error_code, msg_id, task_code, "")

        jHtml = _get_template(ui_texts, error_code)
    except Exception as e:
        error_code = _log_issue(ui_texts, Display.Kind.FATAL, task_code + 1, "", True)
        sidekick.display.fatal(f"{RECEIVE_FILE_DEFAULT_ERROR}: Code {error_code}, Message: {e}.")
        msg = set_msg_fatal("receiveFileException", ui_texts, task_code)
        _, tmpl_ffn, ui_texts = ups_handler(task_code, msg, e)
        jHtml = process_template(tmpl_ffn, **ui_texts)

    return jHtml


# eof
