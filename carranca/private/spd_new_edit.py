"""
Spatial Data Edition

Equipe da Canoa -- 2024
mgd 2024-10-09, 11-12
"""

# cSpell: ignore wtforms formdata urlname gpkg
import os
import json

from os import path
from zlib import crc32
from flask import request
from typing import cast, TypeAlias, Any, Dict, List, Tuple
from wtforms import StringField
from sqlalchemy import func

# It didn't satisfy Pylance, but I'll leave it as info.
FileData: TypeAlias = Dict[str, Any]

from .wtforms import SpdEdit, SpdInsert, apply_lang_to_string_fields
from .spd_analysis import spd_file_format, spd_info_from_file, spd_info_from_bytes
from ..common.UIDBTexts import UIDBTexts
from ..config.FormIcons import FormIcons as fi
from ..helpers.py_helper import is_str_none_or_empty, is_empty
from ..public.ups_handler import get_ups_jHtml
from ..helpers.file_helper import folder_must_exist, get_unique_filename
from ..helpers.types_helper import Route_Response, Choice, Choices
from ..helpers.jinja_helper import process_template
from ..helpers.uiact_helper import UiActResponseProxy
from ..common.app_context_vars import sidekick
from ..helpers.ui_db_texts_manager import set_msg_fatal, UITextsKeys
from ..models.private.spatial_data_file import SpatialDataFile
from ..helpers.route_helper import (
    get_private_response_data,
    get_form_input_value,
    init_response_vars,
    private_route,
    login_route,
    redirect_to,
    home_route,
)
from ..common.app_context_vars import app_user
from ..common.app_error_assistant import ModuleErrorCode, JumpOut
from .spd_analysis import SPD_DATA_KEY_FIELDS

# This name is the standard; until the user informs it, use is.
DEFAULT_ID_ATTRIBUTE_NAME = "id"


def _get_choices(file_data: FileData) -> List[Tuple[str, str]]:
    choices: Choices = sorted(
        [(k, f"{k} | {v['type']}") for k, v in file_data[SPD_DATA_KEY_FIELDS].items() if v["type"] in ["str", "int32"]],
        key=lambda x: x[0],
    )
    return choices


def _do_spd_insert(ui_db_texts: UIDBTexts, spd_row: SpatialDataFile, file_obj: Any, layer: int = 0, analyze_bytes: bool = False) -> bool:
    def __get_extension(fn: str) -> str:
        _, fnx = path.splitext(fn)
        return fnx

    error_msg = ""
    error_code = 0
    ffn = ""
    bytes_format = ""

    try:
        if not file_obj:
            error_code += 1
        elif is_str_none_or_empty(ofn := file_obj.filename):
            # Original file name
            error_code += 2
        elif is_str_none_or_empty(fex := __get_extension(ofn)):
            error_code += 3
        elif is_str_none_or_empty(ufn := get_unique_filename(f"sdf_{app_user.code}_", fex)):
            # Unique file name
            error_code += 4
        elif not folder_must_exist(sidekick.config.LOCAL_SPATIAL_DATA_PATH):
            error_code += 5
        elif len(content := file_obj.read()) < 512:
            error_code += 6
        elif (file_crc32 := crc32(content)) < 0:
            error_code += 7
        elif SpatialDataFile.get_rows([SpatialDataFile.id.key], SpatialDataFile.file_crc32 == file_crc32):
            _, error_msg = ui_db_texts.set_msg_error("errorFileExists", ofn)
            error_code += 8
        elif SpatialDataFile.get_rows([SpatialDataFile.id.key], SpatialDataFile.spd_name_lower == func.lower(spd_row.spd_name)):
            _, error_msg = ui_db_texts.set_msg_error("errorNameExists", spd_row.spd_name)
            error_code += 9
        elif analyze_bytes and not (bytes_format := spd_file_format(fex)):
            # raise Exception(f"Unknown Spatial Data File extension <code>{fex}</code>.")
            error_code += 10
        else:
            error_code += 11
            spd_row.original_file_name = ofn
            # Unique File Name
            spd_row.file_name = ufn
            spd_row.file_crc32 = file_crc32
            spd_row.registered_by = app_user.id
            spd_row.registered_at = func.now()
            ffn = path.join(sidekick.config.LOCAL_SPATIAL_DATA_PATH, ufn)

            # After writing the data, if an error occurs raise exception to delete file
            error_code += 1
            with open(ffn, "wb") as file:
                spd_row.file_size = file.write(content)

            # Assume this fields exists in the layer.
            # Request there values, add 'id' because is typical.
            # Confirmation of the 'real' fields, will be done in spd_edit
            values_from_fields: List[str] = [DEFAULT_ID_ATTRIBUTE_NAME]
            form_field_list = SpdInsert().field_list

            error_code += 1
            for f in form_field_list:
                f_name = getattr(spd_row, f.name)
                if f_name and not f_name in values_from_fields:
                    values_from_fields.append(f_name)

            if analyze_bytes:
                error_code += 1
                spd_data = spd_info_from_bytes(content, bytes_format, layer, values_from_fields)
            else:
                error_code += 2
                spd_data = spd_info_from_file(ffn, layer, values_from_fields)

            if error_info := spd_data["error"]:
                _, error_msg = ui_db_texts.set_msg_error("errorMetadataRead", (ofn, error_info))
                raise Exception(error_msg)

            layer_data = spd_data["layer"]
            spd_row.layer_name = layer_data["name"]
            spd_row.layer_crs = layer_data["crs"]
            spd_row.layer_health = spd_data["health_score"]["score_pct"]
            spd_row.features_count = spd_data["features"]["count"]
            spd_row.file_data = json.dumps(spd_data)

            # Now, we have the real fields list: sanitize attributes
            fields_removed: List[str] = []
            candidates = [k for k, _ in _get_choices(spd_data)]
            for f in form_field_list:
                if getattr(spd_row, f.name) not in candidates:
                    setattr(spd_row, f.name, None)
                    fields_removed.append(f.name)

            error_code = 0
            if fields_removed:
                ui_db_texts.set_msg_success("spdInsertSuccessFields", str(fields_removed))
            else:
                ui_db_texts.set_msg_success("spdInsertSuccess")

    except Exception as e:
        _, error_msg = ui_db_texts.set_msg_error("spdInsertException", (error_code, e))
        sidekick.display.error(error_msg)

    if error_code > 0:
        try:
            # Clean up: delete the file if it was created
            if path.exists(ffn):
                os.remove(ffn)
        except Exception as cleanup_e:
            sidekick.display.error(f"Failed to delete file {ffn}: [{cleanup_e}].")

        if not error_msg:
            _, error_msg = ui_db_texts.set_msg_error("spdInsertError", error_code)

    return is_empty(error_msg)


def _prepare_for_edition(ui_db_texts: UIDBTexts, spd_row: SpatialDataFile, spd_edit_form: SpdEdit):
    "Prepares the data row for a ui edition form"
    error_msg = ""
    error = 30
    file_data: FileData = {}

    def __file_ready(ufn: str) -> int:
        # Unique File Name
        file_error = 0
        ffn = ""
        if not folder_must_exist(sidekick.config.LOCAL_SPATIAL_DATA_PATH):
            file_error += 1
        elif not (ffn := path.join(sidekick.config.LOCAL_SPATIAL_DATA_PATH, ufn)):
            file_error += 2
        elif not path.exists(ffn):
            file_error += 3

        return file_error

    try:
        if not (jsn_data := spd_row.file_data):
            error += 1
        elif not (file_data := json.loads(jsn_data)):
            error += 2
        else:
            error += 3
            choices_with_id = _get_choices(file_data)
            candidates = [k for k, _ in choices_with_id]
            # Only 1 list can have 'id':
            # Remove 'id' from the list, add manually for the first list/select (field_id)
            error += 1
            _id = spd_row.field_id
            if _id in candidates:
                pass
            elif DEFAULT_ID_ATTRIBUTE_NAME in candidates:
                _id = DEFAULT_ID_ATTRIBUTE_NAME
            else:  # use the first item or "" if no items
                if len(candidates) == 0:
                    candidates.append("")
                _id = candidates[0]

            # prepare select options/choices
            # 1) Get the (id, _) tuple that will be the first item of the spd_edit_form.field_list[0]
            error += 1
            first_item: Choice = next(((k, lbl) for k, lbl in choices_with_id if k == _id), (_id, _id))

            # 2) Remove (id, _) item from the list, this is 'choices' for the spd_edit_form.field_list[1], [2]...
            #    but add ("", "") to indicate no value
            choices: Choices = [(k, lbl) for k, lbl in choices_with_id if k != _id]

            # 3) Build the selects
            error += 1
            for field in spd_edit_form.field_list:
                if not any(a == field.data for a, _ in choices):
                    # sanitize attributes, should no happen, thy where sanitized on insert
                    field.data = ""
                field.choices = [first_item] + choices  # pyright: ignore[reportAttributeAccessIssue]
                # After the first select, other selects has there first option empty
                first_item = cast(Choice, ("", ""))

            error += 1
            ui_db_texts["layerNameWithLabel"] = ui_db_texts["layerNameTemplate"].format(file_data["layer"]["name"], len(candidates))  # id

            error += 1
            ufn = spd_row.file_name
            if (code := __file_ready(ufn)) > 0:
                # This is a warning because the file is not needed any more. All relevant data is on the db
                ui_db_texts.set_msg_warn("spdEditFileNotFound", (ufn, code))

            error = 0

        if error > 0 and is_empty(error_msg):
            _, error_msg = ui_db_texts.set_msg_error("spdEditError", error)

    except Exception as e:
        _, error_msg = ui_db_texts.set_msg_error("spdEditException", (e, error))

    return is_empty(error_msg)


def spd_new_or_edit(data: str) -> Route_Response:
    """Spatial DataEdit & Edit Form"""

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
        tmpl_ffn, is_get, ui_db_texts = get_private_response_data("spdNewEdit")

        spd_row: SpatialDataFile | None = SpatialDataFile() if is_insert else SpatialDataFile.get_row(spd_id)
        if spd_row is None:
            raise JumpOut(set_msg_fatal("spdEditNotFound", ui_db_texts), task_code + 1)

        task_code += 1  # 2
        ui_db_texts["insertMode"] = is_insert
        task_code += 1  # 3
        ui_db_texts[UITextsKeys.Form.title] = ui_db_texts[f"formTitle{'New' if is_insert else 'Edit'}"]
        task_code += 1  # 4

        task_code += 1  # 5
        if is_insert:
            fform = SpdInsert(ui_db_texts["insertFieldsPlaceholder"])
            ui_db_texts["fieldListID"] = fform.field_attributes["list"]
        else:  # is_edit:
            fform = SpdEdit()

        apply_lang_to_string_fields(fform, app_user.lang)

        if is_get and is_insert:
            task_code += 1  # 6
        elif is_get and is_edit:
            task_code += 2  # 7
            fform.process(formdata=None, obj=spd_row)
            _prepare_for_edition(ui_db_texts, spd_row, cast(SpdEdit, fform))
        else:  # is_post
            task_code += 3  # 8

            #  helpers
            def __modified(input, field, is_mod):
                if "disabled" in input.render_kw or "readonly" in input.render_kw:
                    return is_mod
                ui_value = get_form_input_value(input.name) if input.type == StringField.__name__ else input.data
                _mod = field != ui_value
                if input.data != ui_value:  # TODO, don't change .data
                    input.data = ui_value

                return is_mod or _mod

            def __save_and_go():
                SpatialDataFile.set_row(spd_row)
                return redirect_to(process_on_end)

            # TODO use flask
            form_modified = is_insert
            for field in fform:
                if hasattr(spd_row, field.name):
                    form_modified = __modified(field, getattr(spd_row, field.name), form_modified)

            if is_insert:
                task_code += 1  # 9
                fform.populate_obj(spd_row)

                file_obj = request.files[(cast(SpdInsert, fform)).upload_file.name] if len(request.files) > 0 else None
                task_code += 1  # 10
                if _do_spd_insert(ui_db_texts, spd_row, file_obj, 0, True):
                    # Edit | review fields
                    fresh_row = cast(SpatialDataFile, SpatialDataFile.set_row(spd_row, True))
                    _prepare_for_edition(ui_db_texts, fresh_row, SpdEdit())

            elif form_modified:
                task_code += 2  # 11
                # CHECK fields_id,  fields_id
                fform.populate_obj(spd_row)
                spd_row.edited_by = app_user.id
                spd_row.edited_at = func.now()
                return __save_and_go()
            else:
                task_code += 3  # 12
                return redirect_to(home_route())

        task_code += 12  # ?
        jHtml = process_template(tmpl_ffn, form=fform, fi=fi.with_icon("spd"), **ui_db_texts.data(), **form_on_close)

    except JumpOut:
        # in an extreme case, tmpl_ffn can be empty
        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("spdEditException", ui_db_texts, task_code, e, "")

    return jHtml


# eof
