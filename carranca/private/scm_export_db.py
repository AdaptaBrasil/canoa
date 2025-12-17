"""
Create/Update Schema & SEP on the Database

mgd 2025.10
"""

# cSpell:ignore zipf

import os
import json
import zipfile
from dataclasses import dataclass

from .scm_data import get_scm_data
from .scm_import import do_scm_import
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
        schema_data, task_code = get_scm_data(task_code, True, config)

        task_code += 1
        # Convert the final object to a JSON string
        schema_dict = class_to_dict(schema_data)

        file_missing = []
        file_info = []
        task_code += 1
        file_data = ExportGrid.get_data(["user_id", "sep_id", "scm_id", "file_origin", "file_name"])

        task_code += 1
        for file in file_data.records:
            ffn = UserFolders(file.user_id).file_full_name(file.file_origin, file.file_name)
            if not os.path.exists(ffn):
                file_missing.append(file.file_name)
            else:
                file_info.append(FileInfo(file.file_name, ffn))

        if len(file_missing) > 0:
            task_code += 1
            add_msg_error("exportError", ui_db_texts, f"<br><br>Missing files: {file_missing}", task_code)
        else:
            task_code += 2
            with zipfile.ZipFile(config.output_full_file_name, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("header.json", json.dumps(config.header, **config.json))
                zipf.writestr("metadata.json", json.dumps(schema_dict, **config.json))
                # Add files from the folder
                for file in file_info:
                    zipf.write(file.ffn, arcname=file.name)

            add_msg_success("exportSuccess", ui_db_texts)

        task_code += 1
        jHtml = process_template(tmpl_ffn, **ui_db_texts.dict())
    except Exception as e:
        jHtml = get_ups_jHtml("exportException", ui_db_texts, task_code, e, task_code)

    return jHtml


# eof
