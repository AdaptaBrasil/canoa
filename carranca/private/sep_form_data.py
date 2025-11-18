"""
SEP Form data for iInsertion & edition


Equipe da Canoa -- 2025
mgd 2025-11-07
"""

from enum import IntEnum
from typing import Tuple
from dataclasses import dataclass

from .wtforms import SepNew
from .SepIconMaker import SepIconMaker
from ..models.public import User
from ..models.private import Sep, Schema, MgmtSepsUser
from ..private.UserSep import UserSep
from ..common.UIDBTexts import UIDBTexts
from ..helpers.py_helper import to_int, clean_text
from ..helpers.types_helper import UsualDict
from ..helpers.route_helper import is_method_get
from ..common.app_context_vars import app_user
from ..common.app_error_assistant import AppStumbled, JumpOut
from ..helpers.ui_db_texts_helper import UITextsKeys, add_msg_final


class SepEditMode(IntEnum):
    NONE = 0
    SIMPLE_EDIT = 100
    FULL_EDIT = 200
    INSERT = 300


@dataclass
class NoManager:
    id: int = 0
    name: str = ""


SCHEMA_LIST_KEY = "schemaList"
SCHEMA_LIST_VALUE = "schemaListValue"
MANAGER_LIST_VALUE = "managerListValue"


def _get_managers(no_manager: NoManager) -> list[UsualDict]:
    user_rows = User.get_all_users(User.disabled == False)
    mng_list = [{"id": no_manager.id, "name": no_manager.name}] + [
        {"id": user.id, "name": user.username} for user in user_rows
    ]
    return mng_list


def get_sep_data(
    task_code: int,
    edit_mode: SepEditMode,
    no_manager: NoManager,
    ui_db_texts: UIDBTexts,
    sep_id: int,
    form: SepNew,
    sep_tmp_name: str,
) -> Tuple[int, UserSep, Sep, UsualDict, str]:
    return_task_code = task_code + 20  # here we can use up to 19
    is_get = is_method_get()
    load_sep_icon_content = not is_get
    sep_row = Sep() if (edit_mode == SepEditMode.INSERT) else Sep.get_row(sep_id, load_sep_icon_content)
    ui_select_lists: UsualDict = {}

    def _get_ui_select_lists(no_scm: list):
        ui_db_texts[SCHEMA_LIST_VALUE] = "" if is_get else str(form.schema_list.data)
        ui_db_texts[MANAGER_LIST_VALUE] = str(no_manager.id if is_get else form.manager_list.data)
        sl = {
            SCHEMA_LIST_KEY: no_scm + Schema.get_schemas(["id", "name"], "name").to_list(),
            "managerList": _get_managers(no_manager),
        }
        return sl

    if sep_row is None:
        # get the editable row
        # Someone deleted just now?
        raise JumpOut(add_msg_final("sepEditNotFound", ui_db_texts), task_code + 1)
    elif edit_mode == SepEditMode.SIMPLE_EDIT:
        # edit only description & icon
        pass
    elif not app_user.is_power:
        # Power user only can edit more fields than description & icon
        raise AppStumbled(add_msg_final("sepNewNotAllow", ui_db_texts), task_code + 2, True)
    elif edit_mode == SepEditMode.FULL_EDIT:
        # edit Scheme (from list), sep name, description & icon
        ui_select_lists = _get_ui_select_lists([])
    elif edit_mode == SepEditMode.INSERT:  # is_insert => return
        # edit Scheme (from list, but force user to select one), sep name, description & icon\
        select_one = ui_db_texts["scm_placeholderOption"]  # (select schema)
        no_scm = [{"id": "", "name": select_one}]
        ui_db_texts[UITextsKeys.Form.icon_url] = ""
        ui_select_lists = _get_ui_select_lists(no_scm)
        return (
            return_task_code,
            None,
            sep_row,
            ui_select_lists,
            ui_db_texts["sepNewTmpName"],
        )  # = 'Novo SEP'
    else:
        raise AppStumbled(add_msg_final("sepNewNotAllow", ui_db_texts), task_code + 5)
    # else is_simple_edit or is_full_edit
    # ------------
    task_code += 6
    # Now, find the sep's manager
    sep_manager: str = ""
    sep_usr_row: MgmtSepsUser = None

    # does current user owns the sep?
    usr_sep = next((sep for sep in app_user.seps if sep.id == sep_id), None)

    # Get fresh dada from db
    if usr_sep is not None:
        # current user owns the sep, so it can be edited, get the record
        sep_usr_row = MgmtSepsUser.get_sep_row(sep_id)
        sep_manager = "" if (edit_mode == SepEditMode.SIMPLE_EDIT) else app_user.name
    elif not app_user.is_power:
        # current user does NOT own the sep, and he is not power user, so can *not* edit it.
        raise JumpOut(
            add_msg_final("sepEditNotAllow", ui_db_texts, sep_tmp_name),
            task_code + 1,
        )
    elif (sep_usr_row := MgmtSepsUser.get_sep_row(sep_id)) is None:
        # the selected sep id was not found
        raise JumpOut(add_msg_final("sepEditNotFound", ui_db_texts), task_code + 2)
    else:
        # create a `usr_sep` and get the sep's manager (user_curr)
        usr_sep_dict = dict(sep_usr_row)
        # Remove 'user_curr' from edit_dict, because is not needed in UserSep(..)
        sep_manager = sep_user if (sep_user := usr_sep_dict.pop("user_curr", None)) else ui_db_texts["managerNone"]
        usr_sep = UserSep(**usr_sep_dict)
        usr_sep.icon_url = SepIconMaker.get_url(usr_sep.icon_file_name)


    # fill the form for edition
    if is_get:
        # set the form's data row for edition, just in case (someone messed with the db) clean up the text
        form.schema_name.data = usr_sep.scm_name
        form.sep_name.data = clean_text(sep_row.name)
        form.visible.data = bool(sep_row.visible)
        form.description.data = clean_text(sep_row.description)
        form.icon_filename.data = None
        form.manager_name.data = sep_manager
        form.manager_name.render_kw["disabled"] = not (edit_mode == SepEditMode.FULL_EDIT)
        if edit_mode == SepEditMode.FULL_EDIT:
            ui_db_texts[SCHEMA_LIST_VALUE] = str(sep_row.id_schema)
            ui_db_texts[MANAGER_LIST_VALUE] = str(to_int(sep_row.users_id, no_manager.id))

        task_code += 3  # 512

    task_code += 1
    ui_db_texts[UITextsKeys.Form.icon_url] = usr_sep.icon_url
    return return_task_code, usr_sep, sep_row, ui_select_lists, sep_usr_row.fullname


# eof
