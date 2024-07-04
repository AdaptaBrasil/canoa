"""
    Initialize the upload file process

    Part of Canoa `File Validation` Processes
    Equipe da Canoa -- 2024
    mgd
"""
# cSpell: ignore werkzeug wtforms uploadfile tmpl

from flask import render_template, request

from .wtforms import UploadFileForm

from ..helpers.py_helper import is_str_none_or_empty
from ..helpers.user_helper import LoggedUser, get_user_receipt
from ..helpers.texts_helper import add_msg_success, add_msg_error
from ..helpers.route_helper import get_private_form_data

def upload_file() -> str:
    template, is_get, texts = get_private_form_data("uploadfile")
    tmpl_form = UploadFileForm(request.form)

    if not is_get:
        from .upload_files.process import process

        ve = texts["validExtensions"]
        valid_extensions = ".zip" if is_str_none_or_empty(ve) else ve.lower().split(",")
        logged_user = LoggedUser()
        file_obj = request.files[tmpl_form.filename.id] if request.files else None
        error_code, msg_error, _, data = process(
            logged_user, file_obj, valid_extensions
        )
        if error_code == 0:
            file_ticket = data.get("file_ticket")
            user_receipt = get_user_receipt(file_ticket)
            log_msg = add_msg_success(
                "uploadFileSuccess", texts, user_receipt, logged_user.email
            )
            # logger(f"Uploadfile: {log_msg}.")
        else:
            log_msg = add_msg_error(msg_error, texts, error_code)
            # logger( f"Uploadfile: {log_msg} | File stage '{_file}' |{removed} Code {task_code} | Exception Error '{except_error}'." )

    return render_template(template, form=tmpl_form, **texts)
