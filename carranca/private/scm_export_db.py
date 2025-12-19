"""
Create/Update Schema & SEP on the Database

mgd 2025.10
"""

# cSpell:ignore zipf arcname

import os
import json
import zipfile
from flask import send_file
from typing import List
from dataclasses import dataclass

from .scm_data import get_scm_data
from ..helpers.py_helper import class_to_dict
from ..public.ups_handler import get_ups_jHtml
from ..helpers.user_helper import UserFolders
from ..helpers.uiact_helper import UiActResponse
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import JinjaGeneratedHtml
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.ui_db_texts_helper import add_msg_error, add_msg_success
from ..config.ExportProcessConfig import ExportProcessConfig
from ..common.app_error_assistant import ModuleErrorCode
from ..models.private_1.ExportGrid import ExportGrid


def scm_export_db(uiact_rsp: UiActResponse) -> JinjaGeneratedHtml:

    @dataclass
    class FileInfo:
        name: str
        ffn: str

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SCM_EXPORT_DB)
    try:
        task_code += 1
        tmpl_ffn, _, ui_db_texts = get_private_response_data("scmExportDB")

        task_code += 1
        config = ExportProcessConfig()

        task_code += 1
        schema_data, task_code = get_scm_data(task_code, config, True)

        task_code += 1
        file_missing = []
        sep_missing = []
        scm_missing = []
        file_info = []
        task_code += 1
        file_data = ExportGrid.get_data(["user_id", "sep_id", "scm_id", "file_origin", "file_name"])

        task_code += 1
        _schemas = schema_data.schemas
        for file  in file_data.records:
            ffn = UserFolders(file.user_id).file_full_name(file.file_origin, file.file_name)
            if (scm := next((item for item in _schemas if item["id"] == file.scm_id), None)) is None:
                scm_missing.append(f"{file.scm_id}")
            elif (sep := next((item for item in scm["seps"] if item["id"] == file.sep_id), None)) is None:
                sep_missing.append(f"{file.sep_id}")
                pass
            elif not os.path.exists(ffn):
                file_missing.append(file.file_name)
            else:
                sep["data_file_name"] = file.file_name
                file_info.append(FileInfo(file.file_name, ffn))

        if len(scm_missing) > 0 or len(sep_missing) > 0 or len(file_missing) > 0:
            task_code += 1

            def _str(what: str, list: List) -> str:
                return f"<br>{what}: [{list}],"

            add_msg_error(
                "exportError",
                ui_db_texts,
                (_str("Files", file_missing) + _str("Schema", scm_missing) + _str("SEP", sep_missing))[:-1],
                task_code,
            )
        else:
            task_code += 2
            schema_dict = class_to_dict(schema_data)
            with zipfile.ZipFile(config.output_full_file_name, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("header.json", json.dumps(config.header, **config.json_cfg))
                zipf.writestr("metadata.json", json.dumps(schema_dict, **config.json_cfg))
                # Add files from the folder
                for file in file_info:
                    zipf.write(file.ffn, arcname=file.name)

            add_msg_success("exportSuccess", ui_db_texts)
            file_response = send_file(config.output_full_file_name, as_attachment=True)
            return file_response

        task_code += 1
        jHtml = process_template(tmpl_ffn, **ui_db_texts.dict())

    except Exception as e:
        jHtml = get_ups_jHtml("exportException", ui_db_texts, task_code, e, task_code)

    return jHtml


# eof
