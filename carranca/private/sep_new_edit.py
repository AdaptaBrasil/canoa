"""
SEP Edition

Equipe da Canoa -- 2024
mgd 2024-10-09, 11-12
mgd 2025-08-19--22  allow edit manager
mgd 2025-11-19 several fixes + refactor -> sep_form_data, sep_icon_data

status
"""

# cSpell: ignore wtforms werkzeug sepsusr usrlist scms nsert


from flask import request
from typing import Tuple, cast
from sqlalchemy import func  # func.now() == server time
from dataclasses import dataclass
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from .wtforms import SepEdit, SepNew
from .sep_icon import icon_refresh
from .SepIconMaker import SepIconMaker
from .sep_icon_data import get_icon_data, IconInfo
from .sep_form_data import get_sep_data, SepEditMode, NoManager, SCHEMA_LIST_KEY
from ..private.UserSep import UserSep
from ..helpers.py_helper import is_str_none_or_empty, to_int
from ..public.ups_handler import get_ups_jHtml
from ..helpers.user_helper import get_batch_code
from ..helpers.uiact_helper import UiActResponseProxy
from ..helpers.jinja_helper import process_template
from ..common.app_context_vars import app_user
from ..helpers.js_consts_helper import js_form_sec_check
from ..common.app_error_assistant import ModuleErrorCode, AppStumbled, JumpOut
from ..helpers.route_helper import (
    get_private_response_data,
    init_response_vars,
    get_form_input_value,
    private_route,
    login_route,
    redirect_to,
)
from ..helpers.ui_db_texts_helper import (
    UITextsKeys,
    add_msg_success,
    add_msg_error,
    add_msg_final,
)


def do_sep_edit(data: str) -> str:
    """SEP Edit & Insert Form"""
    from ..models.private import Sep

    SVG_MIME = "image/svg+xml"

    action, code, row_index = UiActResponseProxy().decode(data)

    if action is not None:  # called from sep_grid
        # TODO use: window.history.back() in JavaScript.
        process_on_end = private_route("sep_grid", code=UiActResponseProxy.show)  # TODO selected Row, ix=row_index)
        form_on_close = {"dlg_close_action_url": process_on_end}
    else:  # standard routine
        code = data
        action = None
        process_on_end = login_route()  # default
        form_on_close = {}  # default = login

    editMode = SepEditMode.NONE
    edit_full_or_ins = True
    if code == UiActResponseProxy.add:
        editMode = SepEditMode.INSERT
    elif app_user.is_power:  #  and is_edit
        editMode = SepEditMode.FULL_EDIT
    else:
        # normal user` can only edit description & icon  fields
        # manager field is hidden, scm & name fields are disabled
        editMode = SepEditMode.SIMPLE_EDIT
        edit_full_or_ins = False

    # edit SEP with ID, is a parameter
    new_sep_id = 0
    sep_id = new_sep_id if (editMode == SepEditMode.INSERT) else UserSep.to_id(code)
    if sep_id is None or sep_id < 0:
        return redirect_to(process_on_end)

    task_code = ModuleErrorCode.SEP_EDIT.value
    jHtml, is_get, ui_db_texts = init_response_vars()
    tmpl_rfn = ""

    # &#8209 is a `nobreak-hyphen`, &hyphen does not work.
    sep_fullname = f"SPC&#8209;{code}"
    try:
        no_manager = NoManager()

        def get_icon_info(form: SepNew | SepEdit) -> IconInfo:
            info = IconInfo()
            form_file_name = form.icon_filename.name
            info.storage = request.files[form_file_name] if form_file_name in request.files else None
            info.sent = info.storage is not None and info.storage.content_type.startswith(SVG_MIME)
            return info

        def _was_form_sep_modified(
            sep_row: Sep, form: SepNew | SepEdit, icon_sent: bool
        ) -> Tuple[bool, bool, str, int, int]:
            if is_get:
                return (False, False, "", -1, -1)

            id_manager, frm_id_schema, frm_sep_name = (None, 0, "")

            if edit_full_or_ins:
                frm_id_manager = cast(int, form.manager_list.data)
                id_manager = None if (frm_id_manager == no_manager.id) else frm_id_manager
                frm_id_schema = cast(int, form.schema_list.data)
                frm_visible = cast(bool, form.visible.data)
                frm_sep_name = get_form_input_value(form.sep_name.name, [Sep.scm_sep])
                frm_description = get_form_input_value(form.description.name)
            else:
                frm_visible = cast(bool, form.visible.data)
                frm_description = get_form_input_value(form.description.name)
                frm_sep_name = sep_row.name

            match editMode:
                case SepEditMode.INSERT:
                    form_modified = True
                    sep_modified = True
                case SepEditMode.SIMPLE_EDIT:
                    form_modified = (
                        (frm_visible != sep_row.visible) or (frm_description != sep_row.description) or icon_sent
                    )
                    sep_modified = False
                case SepEditMode.FULL_EDIT:
                    form_modified = (
                        ((id_manager or sep_row.users_id) and (id_manager != sep_row.users_id))
                        or (frm_id_schema != sep_row.id_schema)
                        or (frm_visible != sep_row.visible)
                        or (frm_sep_name != sep_row.name)
                        or (frm_description != sep_row.description)
                        # keep it last, resource consuming
                        or icon_sent
                    )
                    sep_modified = frm_sep_name != sep_row.name

            # remove spaces & '/' (scm_sep) so the user see its modified values (see get_input_text)
            form.description.data = frm_description
            form.sep_name.data = frm_sep_name
            return form_modified, sep_modified, frm_sep_name, frm_id_schema, id_manager

        task_code += 1  # 1
        tmpl_rfn, is_get, ui_db_texts = get_private_response_data("sepNewEdit")
        if True:  # prepare ui_db_texts & insert & edit form
            no_manager = NoManager(name=ui_db_texts["mng_placeholderOption"])

            ui_db_texts["formForNew"] = edit_full_or_ins
            ui_db_texts["formTitle"] = ui_db_texts[f"formTitle{('New' if editMode == SepEditMode.INSERT else 'Edit')}"]
            task_code += 1  # 2
            form = SepNew(request.form) if edit_full_or_ins else SepEdit(request.form)
            # Personalized template for this user (see tmpl_form.sep_name for more info):
            input_disabled = not app_user.is_power
            form.sep_name.render_kw["disabled"] = input_disabled
            form.sep_name.render_kw["required"] = not input_disabled
            form.sep_name.render_kw["lang"] = app_user.lang
            form.description.render_kw["lang"] = app_user.lang

        task_code += 1  # 3
        sep_row, ui_select_lists, sep_fullname = get_sep_data(
            task_code, editMode, no_manager, ui_db_texts, form, sep_id, sep_fullname
        )

        task_code = ModuleErrorCode.SEP_EDIT.value + 10  # 510
        icon_info = get_icon_info(form)
        form_modified, sep_modified, sep_name, id_schema, id_manager = _was_form_sep_modified(
            sep_row, form, icon_info.sent
        )

        if is_get:
            task_code += 1
        elif not form_modified:
            return redirect_to(process_on_end)
        elif not is_str_none_or_empty(msg_error_key := js_form_sec_check()):
            task_code += 2
            msg_error = add_msg_error(msg_error_key, ui_db_texts)
            raise AppStumbled(msg_error, task_code, True, True)
        elif (
            scm_name := (
                next((scm["name"] for scm in ui_select_lists[SCHEMA_LIST_KEY] if scm["id"] == id_schema), "?")
                if edit_full_or_ins
                else ""
            )
        ) is None:
            # should never happen, is used to keep the if's one level indentation
            pass
        elif sep_modified and Sep.full_name_exists(id_schema, sep_name):
            raise Exception(add_msg_error("sepNameRepeated", ui_db_texts, scm_name, sep_name))
        elif (icon_data := get_icon_data(sep_row, icon_info, form.icon_filename.name)).error_code > 0:
            # msg {ext} [{hint}-{code}]
            raise Exception(
                add_msg_error(
                    "sepEditInvalidFormat", ui_db_texts, SepIconMaker.ext, icon_data.error_hint, icon_data.error_code
                )
            )
        # TODO: Check if icon used (CRC) in other SEP, index is ready
        else:
            task_code += 1  # 511
            sep_row.name = sep_name
            sep_row.visible = bool(form.visible.data)
            sep_row.description = get_form_input_value(form.description.name)
            batch_code = get_batch_code()

            if editMode == SepEditMode.INSERT:
                icon_old_file_name = ""
                sep_row.id = None
                sep_row.visible = True
                sep_row.id_schema = id_schema
                sep_row.ins_by = app_user.id
                sep_row.ins_at = func.now()
            else:
                icon_old_file_name: str = sep_row.icon_file_name
                sep_row.edt_by = app_user.id
                sep_row.edt_at = func.now()

            if edit_full_or_ins:
                task_code += 1  # 512
                # we need `sep_fullname`` in case of error (see except)
                sep_fullname = Sep.get_fullname(scm_name, sep_row.name)
                sep_row.users_id = id_manager

            if schema_changed := ((editMode == SepEditMode.FULL_EDIT) and (id_schema != sep_row.id_schema)):
                sep_row.id_schema = id_schema

            icon_new_file_name = ""
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
                ui_db_texts[UITextsKeys.Form.icon_url] = SepIconMaker.get_url(sep_row.icon_file_name)
                icon_new_file_name = sep_row.icon_file_name

            if (sep_id := Sep.save(sep_row, schema_changed, batch_code)) >= 0:  # :——)
                task_code += 5  # 517
                add_msg_success(
                    "sepSuccessNew" if editMode == SepEditMode.INSERT else "sepSuccessEdit",
                    ui_db_texts,
                    sep_fullname,
                )
                if fresh_icon:  # after post
                    icon_refresh(icon_old_file_name, icon_new_file_name, sep_id)
                if action:
                    return redirect_to(process_on_end)
            else:  # :——(
                task_code += 6  # 19
                item = f"sepFailed{'Edit' if editMode == SepEditMode.SIMPLE_EDIT else 'New'}"
                add_msg_final(item, ui_db_texts, sep_fullname, task_code)

        jHtml = process_template(
            tmpl_rfn,
            form=form,
            **ui_db_texts.dict(),
            **ui_select_lists,
            **form_on_close,
        )

    except JumpOut:
        jHtml = process_template(tmpl_rfn, **ui_db_texts.dict())

    except Exception as e:
        jHtml = get_ups_jHtml("sepEditException", ui_db_texts, task_code, e, task_code, sep_fullname)

    return jHtml


# eof
