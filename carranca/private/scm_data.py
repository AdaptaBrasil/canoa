"""
Schema Data
Collects Schema and all its SEPs data


A json containing the Schema table and its visible SEP is generated.

mgd 2025.08
"""

from typing import Optional, Tuple, Dict, List

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

    def __init__(self, header: Optional[UsualDict], meta_scm: UsualDict, meta_sep: UsualDict, schemas: List[UsualDict]):
        self.coder = None #coder
        self.header = header
        self.meta_scm = meta_scm
        self.meta_sep = meta_sep
        self.schemas = schemas


def scm_data_get(task_code: int, encode64: bool, config: ExportProcessConfig) -> Tuple[SchemaData, int]:
   task_code += 1
   SEPS_KEY = "seps"
   scm_id = SchemaGrid.id.name
   sep_id = Sep.id.name

   task_code += 1
   scm_cols = config.scm_cols.copy()
   sep_cols = config.sep_cols.copy()

   # check if need PK => FK where selected
   task_code += 1
   if scm_id not in scm_cols:
      scm_cols.insert(0, scm_id)

   task_code += 1
   if sep_id not in sep_cols:
      sep_cols.append(sep_id)

   task_code += 1
   scm_rows = SchemaGrid.get_schemas(scm_cols, True)
   schema_list: List[Dict] = []
   sep_rows: List[Sep] = []
   mng_list: Dict = {}

   if Sep.users_id.name in sep_cols:
      user_rows = User.get_all_users(User.disabled == False, User.id)
      mng_list =  {user.id: user.username for user in user_rows}

   get_icon= Sep.icon_file_name.name in sep_cols
   task_code += 1
   mgmt: OptStr = None
   for scm in scm_rows:
      schema_dic = scm.encode64([scm_id]) if encode64 else scm.copy([scm_id])
      schema_dic[SEPS_KEY]: List[Sep] = []
      sep_rows = Sep.get_visible_seps_of_scm(scm.id, sep_cols)
      for sep in sep_rows:
            sep.icon_file_name = do_icon_get_url(sep.icon_file_name, sep.id)  if get_icon else None
            sep.manager = mgmt if mng_list and (mgmt:= mng_list.get(sep.mgmt_users_id)) else "?"
            sep.scm_code = config.coder.encode(scm.id)
            sep.code = config.coder.encode(sep.id)
            schema_dic[SEPS_KEY].append(sep.encode64([sep_id]) if encode64 else sep.copy([sep_id]))

      schema_list.append(schema_dic)

   task_code += 1
   meta_scm = scm_rows.col_info
   meta_sep = sep_rows.col_info if sep_rows else []
   schema_data = SchemaData(config.header, meta_scm, meta_sep, schema_list)

   return schema_data, task_code


# eof