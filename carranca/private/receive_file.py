"""
Initialize the receive file process

Part of Canoa `File Validation` Processes
Equipe da Canoa -- 2024
mgd
"""

# cSpell: ignore werkzeug wtforms tmpl urlname upload_file
import time
import shutil
import mimetypes
from os import path
from math import ceil
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
from ..helpers.file_helper import ensure_folder_exists
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import Jinja_Template, Usual_Dict, Jinja_Rendered
from ..helpers.route_helper import get_private_response_data, get_form_input_value, init_response_vars
from ..helpers.dwnLd_goo_helper import is_gd_url_valid, download_public_google_file
from ..helpers.js_consts_helper import js_ui_dictionary
from .validate_process.ProcessData import ProcessData
from ..helpers.ui_db_texts_manager import UITextsKeys, set_msg_success, set_msg_fatal

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

    # [ "IANA-registered standard", "Legacy Windows non-standard MIME", "...and just in case a new one"]
    valid_content_types = f"application/zip,application/x-zip-compressed,{mimetypes.guess_type("file.zip")}"
    tmpl_ffn = ""
    fform = ReceiveFileForm()
    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.LEGACY_STYLE)

    # utils
    def _get_template(ui_db_texts: UIDBTexts, error_code: int | None) -> Jinja_Rendered:
        seps: "UserSepList" = []
        if error_code is None:
            # msg is ready, just display
            pass
        elif error_code > 0:
            ui_db_texts.set_value(UITextsKeys.Msg.tech, sidekick.log_filename)
        elif not (seps := [sep for sep in app_user.seps]):
            ui_db_texts.set_msg_warn("noSEPassigned")
            seps: "UserSepList" = []
        elif len(seps) > 1:
            sep_placeholder_option = _do_sep_placeholderOption(ui_db_texts.get_str("placeholderOption"))
            seps.insert(0, sep_placeholder_option)

        ui_db_texts.set_value(UITextsKeys.Form.icon_url, seps[0].icon_url if len(seps) > 0 else "")
        if ui_db_texts.display_msg_only:
            fi_icon = ui_db_texts.get

        seps_list: List[Usual_Dict] = [{"code": sep.code, "fullname": sep.fullname, "icon_url": sep.icon_url} for sep in seps]
        tmpl = process_template(tmpl_ffn, form=fform, seps=seps_list, fi=fi.with_icon(), **ui_db_texts.data(), **js_ui_dictionary())
        return tmpl

    def _log_issue(ui_db_texts: UIDBTexts, msg_type: Display.Kind, error_code: int, msg_id: str, task_code: int, msg_arg: str = "") -> int:
        local_error = ModuleErrorCode.RECEIVE_FILE_ADMIT.value + task_code
        show_code = f"{local_error}" if error_code == 0 else f"{error_code}:{task_code}"
        # UPDATE ui_db_texts
        ui_db_texts.reset_messages()
        match msg_type:
            case Display.Kind.WARN:
                _, msg_arg = ui_db_texts.set_msg_warn(msg_id, (show_code, msg_arg))
            case Display.Kind.ERROR:
                _, msg_arg = ui_db_texts.set_msg_error(msg_id, (show_code, msg_arg))
            case Display.Kind.FATAL:
                _, msg_arg = ui_db_texts.set_msg_fatal(msg_id, (show_code, msg_arg))
            case _:
                _, msg_arg = ui_db_texts.set_msg_info(msg_id, (show_code, msg_arg))

        sidekick.display.type(msg_type, msg_arg)
        return local_error

    def _cleanup_user_folders(proc, pd: ProcessData | None, rm_user_folders: bool, rm_lock_folder: bool) -> bool:
        """
        Cleans the three user folders used during the processing and validation of the uploaded file.
        """
        if not pd:
            return False

        def _rm(folder: str):
            kind = sidekick.display.Kind
            _k = kind.FATAL
            try:
                if not path.isdir(folder):
                    result, _k = ("not found.", kind.WARN)
                elif shutil.rmtree(folder) or path.isdir(folder):  # rmtree(folder) -> None
                    result, _k = ("not removed", kind.FATAL)
                else:
                    result, _k = ("removed.", kind.INFO)

                sidekick.display.print(_k, f"[{proc}]: The intermediate process folder '{folder}' was {result}")
            except Exception as e:
                sidekick.display.error(
                    f"[{proc}]: The contents of the intermediate process folders {folder} was *not* removed due to an error: [{e}]."
                )

            return _k in [kind.INFO, kind.WARN]

        _w = True
        _r = True
        _l = True
        if rm_lock_folder:
            _l = _rm(pd.path.data_tunnel_user_lock)

        if rm_user_folders:
            _w = _rm(pd.path.data_tunnel_user_write)
            _r = _rm(pd.path.data_tunnel_user_read)

        return _w and _r and _l  # don't concatenate function ;—)

    def _try_lock_process(ui_db_texts: UIDBTexts, pd: ProcessData, task_code: int) -> bool:
        """
        Checks/acquires the processing lock for a user folder.
        Returns 0 if lock acquired (caller may proceed).
        Returns minutes remaining (>0) if folder is locked by another process.
        Return < 0 if an error occurred
        """

        def _log(remaining_min: int):
            _log_issue(ui_db_texts, Display.Kind.WARN, 0, "receiveFileAdmit_wait", task_code, str(remaining_min))
            ui_db_texts.display_msg_only = True
            return

        result = True
        lock_file = path.join(pd.path.data_tunnel_user_lock, pd.lock.file_name)
        if path.isfile(lock_file):
            age_minutes = (time.time() - path.getmtime(lock_file)) / 60
            if (remaining := pd.lock.ttl_min - age_minutes) > 0:
                _log(ceil(remaining))
                return False

        # stale lock, fall through to delete + recreate
        try:
            open(lock_file, "x").close()
            result = True
        except FileExistsError:
            # lost the race against another request, treat as locked
            _log(pd.lock.ttl_min)
        except Exception as e:
            sidekick.display.error(f"Lock process on folder [{lock_file}] failed: {e}.")
            _log_issue(ui_db_texts, Display.Kind.FATAL, 0, "receiveFileAdmit_bad_lock", task_code)

        return result

    remove_user_folders = True
    pd: ProcessData | None = None
    try:
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("receiveFile")

        if is_get:
            return _get_template(ui_db_texts, 0)

        received_at = now()
        # Find out what was kind of data was sent: an uploaded file or an URL (download)
        file_obj: Any = request.files[fform.upload_file.name] if len(request.files) > 0 else None
        task_code += 1  # 2
        url_str = get_form_input_value(fform.urlname.name)
        task_code += 1  # 3
        has_file = bool(file_obj and getattr(file_obj, "filename", None))
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
            _log_issue(ui_db_texts, Display.Kind.WARN, 0, "receiveFileAdmit_bad_sep", task_code + 1, sep_code)  # 7
            return _get_template(ui_db_texts, 0)
        elif has_file and has_url:
            _log_issue(ui_db_texts, Display.Kind.WARN, 0, "receiveFileAdmit_both", task_code + 2)  # 8
            return _get_template(ui_db_texts, 0)
        elif not (has_file or has_url):
            _log_issue(ui_db_texts, Display.Kind.WARN, 0, "receiveFileAdmit_none", task_code + 3)  # 9
            return _get_template(ui_db_texts, 0)
        elif has_url and is_gd_url_valid(url_str) > 0:
            _log_issue(ui_db_texts, Display.Kind.WARN, 0, "receiveFileAdmit_bad_url", task_code + 4)  # 10
            return _get_template(ui_db_texts, 0)
        elif has_file and file_obj.content_type not in valid_content_types.split(","):
            _log_issue(ui_db_texts, Display.Kind.WARN, 0, "receiveFileAdmit_bad_content_type", task_code + 5)  # 11
            return _get_template(ui_db_texts, 0)

        # Instantiate Process Data helper
        task_code = 13

        def doProcessData() -> Tuple[bool, bool, ProcessData]:
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
            return receive_file_cfg.debug_process, receive_file_cfg.remove_user_folders, pd

        task_code += 1  # 14
        debug_process, remove_user_folders, pd = doProcessData()

        task_code += 1  # 15
        if not ensure_folder_exists(pd.path.data_tunnel_user_lock):
            task_code += 1  # 16
            error_code = _log_issue(ui_db_texts, Display.Kind.ERROR, 0, RECEIVE_FILE_DEFAULT_ERROR, task_code)
            return _get_template(ui_db_texts, error_code)
        elif not _try_lock_process(ui_db_texts, pd, task_code + 2):  # 17
            return _get_template(ui_db_texts, 0)
        elif not _cleanup_user_folders("init:", pd, True, False):
            task_code += 4  # 18
            error_code = _log_issue(ui_db_texts, Display.Kind.FATAL, 0, RECEIVE_FILE_DEFAULT_ERROR, task_code)
            return _get_template(ui_db_texts, error_code)
        elif has_file:
            task_code += 4  # 19
            pd.received_original_name = file_obj.filename
        elif not ensure_folder_exists(pd.path.working_folder):
            task_code += 5  # 20
            error_code = _log_issue(ui_db_texts, Display.Kind.ERROR, 0, RECEIVE_FILE_DEFAULT_ERROR, task_code)
            return _get_template(ui_db_texts, error_code)
        else:
            task_code += 6  # 21
            # {0} Placeholder for the actual file name.
            # Ensures pd.working_file_name() has the correct format.
            pd.received_file_name = "{0}"
            download_code, filename, md = download_public_google_file(
                url_str, pd.path.working_folder, pd.working_file_name(), True, debug_process
            )
            if download_code == 0:
                task_code += 1  # 22
                pd.received_original_name = md["name"]
            else:
                sidekick.display.error(f"Download error code {download_code}.")
                fn = filename if filename else "<ainda sem nome>"
                task_code += 2  # 23
                error_code = _log_issue(ui_db_texts, Display.Kind.ERROR, 0, "receiveFileAdmit_bad_dl", task_code, fn)
                return _get_template(ui_db_texts, error_code)

        pd.received_file_name = secure_filename(pd.received_original_name)
        task_code = 25  # 25
        ve = ui_db_texts["validExtensions"]
        valid_extensions = [".zip"] if is_str_none_or_empty(ve) else ve.lower().split(",")

        task_code += 1  # 24
        error_code, msg_id, _ = process(app_user, sep_data, file_data, pd, received_at, valid_extensions)

        if error_code == 0:
            # log_msg = set_msg_success("uploadFileSuccess", ui_db_texts, pd.user_receipt, app_user.email)
            _, msg = ui_db_texts.set_msg_success("uploadFileSuccess", (pd.user_receipt, app_user.email))
            sidekick.display.debug(msg)
        else:
            _log_issue(ui_db_texts, Display.Kind.FATAL, error_code, msg_id, task_code, "")

        jHtml = _get_template(ui_db_texts, error_code)
    except Exception as e:
        error_code = _log_issue(ui_db_texts, Display.Kind.FATAL, task_code + 1, "", True)
        sidekick.display.fatal(f"{RECEIVE_FILE_DEFAULT_ERROR}: Code {error_code}, Message: {e}.")
        msg = set_msg_fatal("receiveFileException", ui_db_texts, task_code)
        _, tmpl_ffn, ui_db_texts = ups_handler(task_code, msg, e)
        jHtml = process_template(tmpl_ffn, **ui_db_texts)
    finally:
        _cleanup_user_folders("exit", pd, remove_user_folders, True)

    return jHtml


# eof
