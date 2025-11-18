"""
SEP Edition

Equipe da Canoa -- 2024
mgd 2024-10-09, 11-12
"""

# cSpell: ignore wtforms ZáàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ_

from flask import request
from wtforms import StringField
from sqlalchemy import func  # func.now() == db-server time

from .wtforms import ScmEdit
from ..models.private import Schema
from ..public.ups_handler import get_ups_jHtml
from ..helpers.jinja_helper import process_template
from ..helpers.uiact_helper import UiActResponseProxy
from ..helpers.ui_db_texts_helper import add_msg_final
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


def do_scm_edit(data: str) -> str:
    """SCM Edit & Insert Form"""

    action, code, row_index = UiActResponseProxy().decode(data)

    if action is not None:  # called from sep_grid
        # TODO use: window.history.back() in JavaScript.
        process_on_end = private_route("scm_grid", code=UiActResponseProxy.show)  # TODO selected Row, ix=row_index)
        form_on_close = {"dlg_close_action_url": process_on_end}

    else:  # standard routine
        code = data
        action = None
        process_on_end = login_route()  # default
        form_on_close = {}  # default = login

    is_insert = code == UiActResponseProxy.add
    is_edit = not is_insert

    # edit SEP with ID, is a parameter
    new_scm_id = 0
    scm_id = new_scm_id if is_insert else Schema.to_id(code)

    task_code = ModuleErrorCode.SCM_EDIT.value
    jHtml, is_get, ui_db_texts = init_response_vars()

    tmpl_rfn = ""
    try:
        task_code += 1
        tmpl_rfn, is_get, ui_db_texts = get_private_response_data("scmNewEdit")
        form = ScmEdit(request.form)

        if (scm_row := Schema() if is_insert else Schema.get_row(scm_id)) is None:
            # get the editable row
            # Someone deleted just now?
            raise JumpOut(add_msg_final("scmEditNotFound", ui_db_texts), task_code + 1)

        task_code += 1
        ui_db_texts["formTitle"] = ui_db_texts[f"formTitle{'New' if is_insert else 'Edit'}"]
        task_code += 1  # 2

        form.name.render_kw["lang"] = app_user.lang
        form.name.render_kw["pattern"] = ui_db_texts["nameInputPattern"]
        form.name.render_kw["title"] = ui_db_texts["nameErrorHint"]

        form.description.render_kw["lang"] = app_user.lang
        form.content.render_kw["lang"] = app_user.lang
        form.title.render_kw["lang"] = app_user.lang

        if is_get and is_insert:
            scm_row.id = None
            scm_row.visible = False
            scm_row.color = ui_db_texts["colorDefaultValue"]  # "#00000"  # RR GG BB
        elif is_get and is_edit:
            for field in form:
                if hasattr(scm_row, field.name):
                    field.data = getattr(scm_row, field.name)
        else:  # is_post

            def _modified(input, field, is_mod):
                ui_value = get_form_input_value(input.name, None) if input.type == StringField.__name__ else input.data
                _mod = field != ui_value
                if input.data != ui_value:  # TODO, don't change .data
                    input.data = ui_value

                return is_mod or _mod

            # TODO make a helper
            form_modified = is_insert
            for field in form:
                if hasattr(scm_row, field.name):
                    form_modified = _modified(field, getattr(scm_row, field.name), form_modified)

            def _save_and_go():
                form.populate_obj(scm_row)
                #  scm_row.visible = scm_row.visible == "y"  # TODO
                scm_row.color = scm_row.color.upper()
                Schema.save(scm_row)
                return redirect_to(process_on_end)

            if is_insert:
                scm_row.ins_by = app_user.id
                scm_row.ins_at = func.now()
                task_code += 1
                return _save_and_go()
            elif form_modified:
                scm_row.edt_by = app_user.id
                scm_row.edt_at = func.now()
                task_code += 2
                return _save_and_go()
            else:
                return redirect_to(home_route())

        jHtml = process_template(tmpl_rfn, form=form, **ui_db_texts.dict(), **form_on_close)

    except JumpOut:
        # in an extreme case, tmpl_rfn can be empty
        jHtml = process_template(tmpl_rfn, **ui_db_texts.dict())

    except Exception as e:
        jHtml = get_ups_jHtml("scmEditException", ui_db_texts, task_code, e)

    return jHtml


# eof
