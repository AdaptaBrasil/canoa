"""
Spatial Data Edition

Equipe da Canoa -- 2024
mgd 2024-10-09, 11-12
"""

# cSpell: ignore wtforms formdata

from wtforms import StringField
from sqlalchemy import func

from .wtforms import SpdEdit
from ..public.ups_handler import get_ups_jHtml
from ..helpers.types_helper import Route_Response
from ..helpers.jinja_helper import process_template
from ..helpers.uiact_helper import UiActResponseProxy
from ..helpers.ui_db_texts_manager import set_msg_fatal
from ..models.private.spatial_data_file import SpatialDataFile
from ..helpers.route_helper import (
    get_private_response_data,
    init_response_vars,
    get_form_input_value,
    private_route,
    login_route,
    redirect_to,
    home_route,
)

from ..common.app_context_vars import app_user
from ..common.app_error_assistant import ModuleErrorCode, JumpOut


def do_spd_edit(data: str) -> Route_Response:
    """Spatial DataEdit & Insert Form"""

    action, code, row_index = UiActResponseProxy().decode(data)

    if action is not None:  # called from sep_grid
        # TODO use: window.history.back() in JavaScript.
        # TODO selected Row, ix=row_index)
        process_on_end = private_route("spd_grid", code=UiActResponseProxy.show)
        form_on_close = {"dlgFormCloseAction": process_on_end}
    else:  # standard routine
        code = data
        action = None
        process_on_end = login_route()  # default
        form_on_close = {}  # default = login

    is_insert = code == UiActResponseProxy.add
    is_edit = not is_insert

    # edit SEP with ID, is a parameter
    new_spd_id = 0
    spd_id = new_spd_id if is_insert else SpatialDataFile.to_id(code)

    jHtml, is_get, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SPD_EDIT)

    tmpl_ffn = ""
    try:
        task_code += 1
        fform = SpdEdit()
        task_code += 1  # 2
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("spdNewEdit")

        if (spd_row := SpatialDataFile() if is_insert else SpatialDataFile.get_row(spd_id)) is None:
            # get the editable row
            # Someone deleted just now?
            raise JumpOut(set_msg_fatal("spdEditNotFound", ui_db_texts), task_code + 1)

        task_code += 1  # 3
        ui_db_texts["formTitle"] = ui_db_texts[f"formTitle{'New' if is_insert else 'Edit'}"]
        task_code += 1  # 4
        ui_db_texts["fieldListID"] = fform.field_attributes["list"]

        fform.name.render_kw["lang"] = app_user.lang
        fform.description.render_kw["lang"] = app_user.lang
        fform.title.render_kw["lang"] = app_user.lang

        if is_get and is_insert:
            task_code += 1  # 5
        elif is_get and is_edit:
            task_code += 2  # 6
            fform.process(formdata=None, obj=spd_row)
            # for field in fform:
            #     if hasattr(spd_row, field.name):
            #         field.data = getattr(spd_row, field.name)
        else:  # is_post
            task_code += 3  # 7

            #  helpers
            def __modified(input, field, is_mod):
                ui_value = get_form_input_value(input.name) if input.type == StringField.__name__ else input.data
                _mod = field != ui_value
                if input.data != ui_value:  # TODO, don't change .data
                    input.data = ui_value

                return is_mod or _mod

            def __save_and_go():
                fform.populate_obj(spd_row)
                SpatialDataFile.set_row(spd_row)
                return redirect_to(process_on_end)

            # TODO make a helper
            form_modified = is_insert
            for field in fform:
                if hasattr(spd_row, field.name):
                    form_modified = __modified(field, getattr(spd_row, field.name), form_modified)

            if is_insert:
                task_code += 1  # 8
                spd_row.registered_by = app_user.id
                spd_row.registered_at = func.now()
                spd_row.file_name = "xx"
                spd_row.file_size = 99001
                spd_row.file_crc32 = 123
                spd_row.ticket = 'kxx'

                return __save_and_go()
            elif form_modified:
                task_code += 2  # 9
                spd_row.edited_by = app_user.id
                spd_row.edited_at = func.now()
                return __save_and_go()
            else:
                task_code += 1  # 10
                return redirect_to(home_route())

        task_code += 12  # ?
        jHtml = process_template(tmpl_ffn, form=fform, **ui_db_texts.data(), **form_on_close)

    except JumpOut:
        # in an extreme case, tmpl_ffn can be empty
        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("spdEditException", ui_db_texts, task_code, e, "")

    return jHtml


# eof
