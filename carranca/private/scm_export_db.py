"""
Create/Update Schema & SEP on the Database

mgd 2025.10
"""

import json

from .scm_data import scm_data_get
from ..helpers.py_helper import class_to_dict
from ..public.ups_handler import get_ups_jHtml
from ..helpers.uiact_helper import UiActResponse
from ..helpers.jinja_helper import process_template
from ..helpers.types_helper import JinjaGeneratedHtml
from ..helpers.route_helper import get_private_response_data, init_response_vars
from ..helpers.ui_db_texts_helper import add_msg_error, add_msg_success
from ..config.ExportProcessConfig import ExportProcessConfig
from ..common.app_error_assistant import ModuleErrorCode


def scm_export_db(uiact_rsp: UiActResponse) -> JinjaGeneratedHtml:

    task_code = ModuleErrorCode.SCM_EXPORT_DB
    jHtml, _, ui_db_texts = init_response_vars()

    try:
        task_code += 1
        tmpl_rfn, _, ui_db_texts = get_private_response_data("scmExportDB")

        task_code += 1
        config = ExportProcessConfig()
        task_code += 1
        schema_data, task_code = scm_data_get(task_code, True, config)

        task_code += 1
        if False:
            # Convert the final dictionary to a JSON string
            data = class_to_dict(schema_data)
            jsn_data = json.dumps(data, **config.json)
            from .scm_import import do_scm_import

            # recover coder n case is needed
            schema_data.coder = coder

            dic_data = do_scm_import(jsn_data)
            # Convert to SQL statements
            print(dic_data)

        # if success:
        add_msg_success("exportSuccess", ui_db_texts)

        # if error:
        add_msg_error("exportError", ui_db_texts, "'Nome de esquema repetido.'", task_code)

        task_code += 1
        jHtml = process_template(tmpl_rfn, **ui_db_texts.dict())
    except Exception as e:
        jHtml = get_ups_jHtml("exportException", ui_db_texts, task_code, e)

    return jHtml


# eof
