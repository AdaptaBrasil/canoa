"""
Create/Update Schema & SEP on the Database

mgd 2025.10
"""

# cSpell:ignore zipf arcname

import os
import json
import zipfile
from flask import Response, send_file
from typing import List
from dataclasses import dataclass

from .scm_data import get_scm_data
from ..helpers.py_helper import class_to_dict
from ..common.ups_handler import get_ups_jHtml
from ..helpers.user_helper import UserFolders
from ..helpers.uiact_helper import UiActResponse
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import Jinja_Rendered
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..models.private.ExportGrid import ExportGrid
from ..config.ExportProcessConfig import ExportProcessConfig
from ..common.app_error_assistant import ModuleErrorCode


def scm_export_db(uiact_rsp: UiActResponse) -> Jinja_Rendered | Response:

    @dataclass
    class FileInfo:
        name: str
        ffn: str

    jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.SCM_EXPORT_DB)
    try:
        task_code += 1
        tmpl_ffn, _, ui_db_texts = get_private_response_data("scmExportDB")
        task_code += 1
        config = ExportProcessConfig(True)
        task_code += 1
        schema_data, task_code = get_scm_data(task_code, config, True)

        task_code += 1
        file_missing = []
        sep_missing = []
        scm_missing = []
        file_info = []
        task_code += 1

        @dataclass(slots=True)
        class GridFields:
            user_id: int
            sep_id: int
            scm_id: int
            file_origin: str
            file_name: str

        grid_data = ExportGrid.get_rows(GridFields, ExportGrid.is_exportable == True)

        task_code += 1
        _schemas = schema_data.schemas
        for row in grid_data.records:
            ffn = UserFolders(row.user_id).file_full_name(row.file_origin, row.file_name)
            if (scm := next((item for item in _schemas if item["id"] == row.scm_id), None)) is None:
                scm_missing.append(f"{row.scm_id}")
            elif (sep := next((item for item in scm["seps"] if item["id"] == row.sep_id), None)) is None:
                sep_missing.append(f"{row.sep_id}")
                pass
            elif not os.path.exists(ffn):
                file_missing.append(row.file_name)
            else:
                sep["data_file_name"] = row.file_name
                file_info.append(FileInfo(row.file_name, ffn))

        if len(scm_missing) > 0 or len(sep_missing) > 0 or len(file_missing) > 0:
            task_code += 1

            def _str(what: str, list: List) -> str:
                return f"<br>{what}: [{list}],"

            missing_msg = (_str("Files", file_missing) + _str("Schema", scm_missing) + _str("SEP", sep_missing))[:-1]
            ui_db_texts.set_msg_error("msgError", (missing_msg, task_code))
        else:
            task_code += 2
            schema_dict = class_to_dict(schema_data)
            with zipfile.ZipFile(config.output_full_file_name, "w", zipfile.ZIP_DEFLATED) as zipf:
                # zipf.writestr("header.json", json.dumps(config.header, **config.json_cfg))
                zipf.writestr("metadata.json", json.dumps(schema_dict, **config.json_cfg))
                # Add files from the folder
                for row in file_info:
                    zipf.write(row.ffn, arcname=row.name)

            ui_db_texts.set_msg_success()
            file_response = send_file(config.output_full_file_name, as_attachment=True)
            return file_response

        task_code += 1
        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("msgFatal", ui_db_texts, task_code, e)

    return jHtml


# eof
