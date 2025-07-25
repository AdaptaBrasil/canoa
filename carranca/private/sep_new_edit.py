"""
SEP Edition

Equipe da Canoa -- 2024
mgd 2024-10-09, 11-12
"""

# cSpell: ignore wtforms werkzeug sepsusr usrlist scms nsert

import re
from flask import request
from typing import Tuple
from os.path import splitext
from sqlalchemy import func  # func.now() == server time
from dataclasses import dataclass
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from .wtforms import SepEdit, SepNew

from .sep_icon import icon_refresh, ICON_MIN_SIZE
from .SepIconMaker import SepIconMaker
from .sep_constants import SEP_CMD_GRD, SEP_CMD_INS, ACTION_CODE_SEPARATOR
from ..models.private import Sep, Schema, MgmtSepsUser
from ..private.UserSep import UserSep
from ..helpers.py_helper import clean_text, to_int, crc16
from ..public.ups_handler import ups_handler
from ..helpers.user_helper import get_batch_code
from ..helpers.jinja_helper import process_template
from ..helpers.route_helper import (
    get_private_response_data,
    init_response_vars,
    get_front_end_str,
    login_route,
    private_route,
    redirect_to,
)

from ..common.app_context_vars import app_user
from ..common.app_error_assistant import ModuleErrorCode, AppStumbled, JumpOut
from ..helpers.ui_db_texts_helper import (
    UITextsKeys,
    add_msg_success,
    add_msg_error,
    add_msg_final,
)


SVG_MIME = "image/svg+xml"
SCHEMA_LIST = "schemaList"
SCHEMA_LIST_VALUE = "schemaListValue"


def do_sep_edit(data: str) -> str:
    """SEP Edit Form"""

    @dataclass
    class IconData:
        content: str = ""
        file_name: str = ""
        ready: bool = False
        crc: int = 0
        error_hint: str = ""
        error_code: int = 0

    new_sep_id = 0
    row_index = None

    if ACTION_CODE_SEPARATOR in data:  # called from sep_grid
        """
        action:code
        -----------
        `action` can be:
            » None: is a call from the menu, no action.
              After edit or insert, return to standard login()
                or
            » [C]reate, [I]nsert, [E]dit
            It is the first char of the button that trigger the action in
                `private/sep_grid.html.j2`
            and routed here via
                `private/rout("/sep_grid/<code>")`
            See sep_grid.html.j2  { -- Action Triggers -- }
            After edit or insert, return to the calling grid & select this row
        """
        action = data.split(ACTION_CODE_SEPARATOR)[0]

        """
        `code` can be:
            » SEP_CMD_INS : insert a new SEP
              or
            » The obfuscate ID of the SEP to edit
        """
        code = data.split(ACTION_CODE_SEPARATOR)[1]

        """
        `row_index` is the selected row index, selected again on return
        # TODO, now optional
        """
        row_index = f"{data}{ACTION_CODE_SEPARATOR}".split(ACTION_CODE_SEPARATOR)[2]

        """
            Where to go after:
                - save: goto
                - close: on_close
        """
        # TODO use: window.history.back() in JavaScript.
        process_on_end = private_route("sep_grid", code=SEP_CMD_GRD)  # TODO selected Row, ix=row_index)

        form_on_close = {"action_form__form_on_close": process_on_end}

    else:  # standard routine
        code = data
        action = None
        process_on_end = login_route()  # default
        form_on_close = {}  # default = login

    is_full_edit = False
    is_simple_edit = False
    is_insert = code == SEP_CMD_INS
    if is_insert:
        # insert can modified all fields (readonly `manager`` not shown)
        pass
    elif app_user.is_power:
        # full edit can edit all fields but `manager`` that is readonly (see .sep_mgmt)
        is_full_edit = True
    else:
        # `normal user` can only edit description & icon
        is_simple_edit = True

    # edit SEP with ID, is a parameter
    sep_id = new_sep_id if is_insert else UserSep.to_id(code)
    if sep_id is None or sep_id < 0:
        return redirect_to(process_on_end)

    task_code = ModuleErrorCode.SEP_EDIT.value
    flask_form, tmpl_ffn, is_get, ui_texts = init_response_vars()
    sep_fullname = f"SPC&#8209;{code}"  # &#8209 is a `nobreak-hyphen`, &hyphen does not work.
    tmpl = ""
    try:

        def was_icon_file_sent() -> Tuple[bool, FileStorage | None]:
            form_file_name = flask_form.icon_filename.name
            file_storage: FileStorage = (
                request.files[form_file_name] if form_file_name in request.files else None
            )
            icon_file_sent = file_storage is not None and file_storage.content_type.startswith(SVG_MIME)
            return icon_file_sent, file_storage

        def _get_sep_data(load_sep_icon_content: bool, task_code: int) -> Tuple[UserSep, Sep, int, str]:

            if (sep_row := Sep() if is_insert else Sep.get_row(sep_id, load_sep_icon_content)) is None:
                # get the editable row
                # Someone deleted just now?
                raise JumpOut(add_msg_final("sepEditNotFound", ui_texts), task_code + 1)
            elif is_simple_edit:
                # edit only description & icon
                ui_texts[SCHEMA_LIST] = []
                pass
            elif not app_user.is_power:
                # Power user only can edit more fields than description & icon
                raise AppStumbled(add_msg_final("sepNewNotAllow", ui_texts), task_code + 2, True)
            elif is_full_edit:
                # edit Scheme (from list), sep name, description & icon
                ui_texts[SCHEMA_LIST_VALUE] = "" if is_get else flask_form.schema_list.data
                ui_texts[SCHEMA_LIST] = Schema.get_schemas().to_list()
            else:  # is_insert => return
                # edit Scheme (from list, but force user to select one), sep name, description & icon
                ui_texts[SCHEMA_LIST_VALUE] = "" if is_get else flask_form.schema_list.data
                ui_texts[UITextsKeys.Form.icon_url] = SepIconMaker.get_url(SepIconMaker.empty_file)
                select_one = ui_texts["placeholderOption"]  # (select schema)
                ui_texts[SCHEMA_LIST] = [{"id": "", "name": select_one}] + Schema.get_schemas().to_list()
                return None, sep_row, task_code + 10, ui_texts["sepNewTmpName"]

            # else is_simple_edit or is_full_edit
            # ------------
            task_code += 3
            # Now, find the sep's manager
            sep_manager: str = None
            sep_usr_row: MgmtSepsUser = None

            # does current user owns the sep?
            usr_sep = next((sep for sep in app_user.seps if sep.id == sep_id), None)

            # Get fresh dada from db
            if usr_sep is not None:
                # current user owns the sep, so it can be edited, get the record
                sep_usr_row = MgmtSepsUser.get_sep_row(sep_id)
                sep_manager = app_user.name
            elif not app_user.is_power:
                # current user does NOT own the sep, and he is not power user, so can *not* edit it.
                raise JumpOut(add_msg_final("sepEditNotAllow", ui_texts, sep_fullname), task_code + 1)
            elif (sep_usr_row := MgmtSepsUser.get_sep_row(sep_id)) is None:
                # the selected sep id was not found
                raise JumpOut(add_msg_final("sepEditNotFound", ui_texts), task_code + 2)
            else:
                # create a `usr_sep` and get the sep's manager (user_curr)
                usr_sep_dict = dict(sep_usr_row)
                # Remove 'user_curr' from edit_dict, because is not needed in UserSep(..)
                sep_manager = (
                    sep_user
                    if (sep_user := usr_sep_dict.pop("user_curr", None))
                    else ui_texts["managerNone"]
                )
                usr_sep = UserSep(**usr_sep_dict)
                usr_sep.icon_url = SepIconMaker.get_url(usr_sep.icon_file_name)

            # => usr_sep, sep_manager & sep_usr_row are ready always

            # fill the form for edition
            if is_get:
                # set the form's data row for edition, just in case (someone messed with the db) clean up the text
                flask_form.schema_name.data = usr_sep.scm_name
                flask_form.sep_name.data = clean_text(sep_row.name)
                flask_form.visible.data = bool(sep_row.visible)
                flask_form.description.data = clean_text(sep_row.description)
                flask_form.icon_filename.data = None
                flask_form.manager_name.data = None
                if is_full_edit:
                    ui_texts[SCHEMA_LIST_VALUE] = sep_row.id_schema
                    flask_form.manager_name.data = sep_manager

                task_code += 3  # 509

            task_code += 1
            ui_texts[UITextsKeys.Form.icon_url] = usr_sep.icon_url
            return usr_sep, sep_row, task_code, sep_usr_row.fullname

        def _was_form_sep_modified(sep_row: Sep) -> Tuple[bool, bool]:
            # remove schema/sep separator sep+sep
            ui_sep_name = get_front_end_str(flask_form.sep_name.name, [Sep.scm_sep])
            ui_description = get_front_end_str(flask_form.description.name)

            if is_insert:
                id_schema = flask_form.schema_list.data
                sep_modified = True
                form_modified = id_schema or ui_description or ui_sep_name
            else:  # is_edit or is_full_edit
                # TODO check Schema
                sep_name = sep_row.name if ui_sep_name is None else ui_sep_name
                flask_form.sep_name.data = sep_name
                id_schema = flask_form.schema_list.data if is_full_edit else sep_row.id_schema
                sep_modified = not (sep_name == sep_row.name)
                form_modified = (
                    sep_modified
                    or (ui_description != sep_row.description)
                    or (id_schema != sep_row.id_schema)
                    or (flask_form.visible.data != sep_row.visible)
                    or was_icon_file_sent()[0]  # keep it as the last test (resource)
                )

            # remove spaces & '/' (scm_sep) so the user see its modified values (see get_input_text)
            flask_form.description.data = ui_description
            flask_form.sep_name.data = ui_sep_name
            return form_modified, sep_modified, id_schema

        def _get_icon_data(sep_row: Sep) -> IconData:
            def __find(pattern: str, data: str) -> int:
                match = re.search(pattern, data, re.IGNORECASE | re.DOTALL)
                return match.start() if match else -1

            icon_file_sent, file_storage = was_icon_file_sent()
            icon_data = IconData(file_name=file_storage.filename)
            expected_ext = f".{SepIconMaker.ext}".lower()

            if not icon_file_sent:
                pass
            elif not splitext(icon_data.file_name)[1].lower().endswith(expected_ext):
                icon_data.error_hint = expected_ext
                icon_data.error_code = 1
            elif not (file_obj := request.files.get(flask_form.icon_filename.name)):
                icon_data.error_hint = "↑×"
                icon_data.error_code = 2
            elif len(data := file_obj.read().decode("utf-8").strip()) < ICON_MIN_SIZE:
                icon_data.error_hint = f"≤ {ICON_MIN_SIZE}"
                icon_data.error_code = 3
            elif (start := __find(r"<svg.*?>", data)) < 0:
                icon_data.error_hint = "¿<svg>"
                icon_data.error_code = 4
            elif (end := __find(r"</svg\s*>", data)) < 0:
                icon_data.error_hint = "</svg>?"
                icon_data.error_code = 5
            elif (end - start) < ICON_MIN_SIZE:
                icon_data.error_hint = f"< {ICON_MIN_SIZE}"
                icon_data.error_code = 6
            elif not (sep_row.icon_svg or "") == (data or ""):
                icon_data.content = data
                icon_data.crc = crc16(data)
                icon_data.ready = True

            return icon_data

        task_code += 1  # 1
        tmpl_ffn, is_get, ui_texts = get_private_response_data("sepNewEdit")
        ui_texts["formForNew"] = is_insert or is_full_edit
        ui_texts["formTitle"] = ui_texts[f"formTitle{('New' if is_insert else 'Edit')}"]
        task_code += 1  # 2
        flask_form = SepNew(request.form) if is_insert or is_full_edit else SepEdit(request.form)
        # Personalized template for this user (see tmpl_form.sep_name for more info):
        input_disabled = not app_user.is_power
        flask_form.sep_name.render_kw["disabled"] = input_disabled
        flask_form.sep_name.render_kw["required"] = not input_disabled
        flask_form.sep_name.render_kw["lang"] = app_user.lang
        flask_form.description.render_kw["lang"] = app_user.lang

        task_code += 1  # 3
        usr_sep, sep_row, task_code, sep_fullname = _get_sep_data(not is_get, task_code)

        task_code = ModuleErrorCode.SEP_EDIT.value + 10  # 510
        form_mod, sep_mod, id_schema = (False, False, -1) if is_get else _was_form_sep_modified(sep_row)

        sep_name = usr_sep.name if input_disabled else flask_form.sep_name.data
        scm_name = next((scm["name"] for scm in ui_texts[SCHEMA_LIST] if scm["id"] == id_schema), "?")

        if is_get:
            task_code += 1
        elif not form_mod:
            # TODO: nothing modified, add_msg_warn("nothingChanged", ui_texts)
            return redirect_to(process_on_end)
        elif (is_insert or sep_mod) and Sep.full_name_exists(id_schema, sep_name):
            add_msg_error("sepNameRepeated", ui_texts, scm_name, sep_name)
        elif (icon_data := _get_icon_data(sep_row)).error_code > 0:
            # msg {ext} [{hint}-{code}]
            add_msg_error(
                "sepEditInvalidFormat",
                ui_texts,
                SepIconMaker.ext,
                icon_data.error_hint,
                icon_data.error_code,
            )
        # TODO: Check if icon used (CRC) in other SEP, index is ready
        else:
            task_code += 1  # 511
            sep_row.name = sep_name
            sep_row.visible = bool(flask_form.visible.data)
            sep_row.description = get_front_end_str(flask_form.description.name)
            batch_code = get_batch_code()

            if is_insert:
                icon_old_file_name = None
                sep_row.id = None
                sep_row.visible = True
                sep_row.id_schema = id_schema
                sep_row.ins_by = app_user.id
                sep_row.ins_at = func.now()
            else:
                icon_old_file_name = sep_row.icon_file_name
                sep_row.edt_by = app_user.id
                sep_row.edt_at = func.now()

            if is_insert or is_full_edit:
                task_code += 1  # 512
                # we need `sep_fullname`` in case of error (see except)
                sep_fullname = Sep.get_fullname(scm_name, sep_row.name)

            if schema_changed := (is_full_edit and (id_schema != sep_row.id_schema)):
                sep_row.id_schema = id_schema

            icon_new_file_name = None
            if fresh_icon := icon_data.ready:
                task_code += 4  # 516
                sep_row.icon_svg = icon_data.content
                sep_row.icon_crc = icon_data.crc
                sep_row.icon_file_name = f"{batch_code}-{icon_data.crc:04x}_sep.{SepIconMaker.ext}"
                sep_row.icon_uploaded_at = func.now()
                sep_row.icon_original_name = secure_filename(icon_data.file_name)
                sep_row.ico_by = app_user.id
                sep_row.ico_at = func.now()
                sep_row.icon_version = to_int(sep_row.icon_version, 0) + 1
                ui_texts[UITextsKeys.Form.icon_url] = SepIconMaker.get_url(sep_row.icon_file_name)
                icon_new_file_name = sep_row.icon_file_name

            if (sep_id := Sep.save(sep_row, schema_changed, batch_code)) >= 0:  # :——)
                task_code += 5  # 21
                add_msg_success("sepSuccessNew" if is_insert else "sepSuccessEdit", ui_texts, sep_fullname)
                if fresh_icon:  # after post
                    icon_refresh(icon_old_file_name, icon_new_file_name, sep_id)
                if action:
                    return redirect_to(process_on_end)
            else:  # :——(
                task_code += 6  # 19
                item = f"sepFailed{'Edit' if is_simple_edit else 'New'}"
                add_msg_final(item, ui_texts, sep_fullname, task_code)

        tmpl = process_template(tmpl_ffn, form=flask_form, **ui_texts, **form_on_close)

    except JumpOut:
        tmpl = process_template(tmpl_ffn, **ui_texts)

    except Exception as e:
        item = add_msg_final("sepEditException", ui_texts, sep_fullname, task_code)
        _, tmpl_ffn, ui_texts = ups_handler(task_code, item, e)
        tmpl = process_template(tmpl_ffn, **ui_texts)

    return tmpl


# eof
