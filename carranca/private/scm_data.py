"""
Schema Data
Collects Schema and all its SEPs data


A json containing the Schema table and its visible SEP is generated.

mgd 2025.08
"""

from typing import Optional, Tuple, Dict, List
from pathlib import Path

from .sep_icon import do_icon_get_url
from ..models.public import User
from ..models.private import Sep
from ..helpers.py_helper import UsualDict
from ..helpers.types_helper import OptStr
from ..config.ExportProcessConfig import ExportProcessConfig
from ..models.private_1.SchemaGrid import SchemaGrid


class SchemaData:
    header: Optional[UsualDict]
    meta_scm: UsualDict
    meta_sep: UsualDict
    schemas: List[UsualDict]

    def __init__(
        self,
        header: Optional[UsualDict],
        meta_scm: UsualDict,
        meta_sep: UsualDict,
        schemas: List[UsualDict],
    ):
        self.coder = None  # coder
        self.header = header
        self.meta_scm = meta_scm
        self.meta_sep = meta_sep
        self.schemas = schemas


def get_scm_data(task_code: int, config: ExportProcessConfig, for_export: bool) -> Tuple[SchemaData, int]:
    task_code += 1
    scm_id = SchemaGrid.id.name
    sep_id = Sep.id.name

    task_code += 1
    scm_cols = config.scm_cols
    sep_cols = config.sep_cols

    # check if need PK => FK where selected
    task_code += 1
    if scm_id not in scm_cols:
        scm_cols.insert(0, scm_id)

    task_code += 1
    if sep_id not in sep_cols:
        sep_cols.insert(0, sep_id)

    task_code += 1
    scm_rows = SchemaGrid.get_schemas(scm_cols, True)
    schema_list: List[Dict] = []
    sep_rows: List[Sep] = []
    mgmt_list: Dict = {}

    if Sep.users_id.name in sep_cols:
        user_rows = User.get_all_users(User.disabled == False, User.id)
        mgmt_list = {user.id: user.username for user in user_rows}

    get_icon = Sep.icon_file_name.name in sep_cols
    task_code += 1
    mgmt: OptStr = None
    scm_col_ign = [] if for_export else [scm_id]
    sep_col_ign = [] if for_export else [sep_id]
    for scm in scm_rows:
        schema_dic = scm.encode64(scm_col_ign) if config.encode_data else scm.copy(scm_col_ign)
        seps: List["Sep"] = []
        # schema_dic[config.seps_key]: List["Sep"] = []
        sep_rows = Sep.get_visible_seps_of_scm(scm.id, sep_cols)
        for sep in sep_rows:
            sep.icon_file_name = do_icon_get_url(sep.icon_file_name, sep.id) if get_icon else None
            sep.manager = mgmt if mgmt_list and (mgmt := mgmt_list.get(sep.mgmt_users_id)) else "?"
            if for_export:
                sep.data_file_name = None
                sep.icon_file_name =  Path(sep.icon_file_name).name
            else:
                sep.scm_code = config.coder.encode(scm.id)
                sep.code = config.coder.encode(sep.id)

            seps.append(sep.encode64(sep_col_ign) if config.encode_data else sep.copy(sep_col_ign))

        schema_dic[config.seps_key] = seps
        schema_list.append(schema_dic)

    task_code += 1
    meta_scm = scm_rows.col_info
    task_code += 1
    meta_sep = sep_rows.col_info if sep_rows else []
    task_code += 1
    schema_data = SchemaData(config.header, meta_scm, meta_sep, schema_list)

    return schema_data, task_code


# eof
