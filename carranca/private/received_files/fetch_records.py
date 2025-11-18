"""
User's Received Files's Management

    Fetch one record (by id) or all records for a user_id

Equipe da Canoa -- 2025
mgd 2025-01-14 & 03-18
"""

from os import path
from typing import Tuple, Optional
from ...models.private import ReceivedFiles
from ...common.app_context_vars import app_user
from ...config.ValidateProcessConfig import ValidateProcessConfig

from ...helpers.user_helper import UserFolders, get_user_folder
from ...helpers.file_helper import change_file_ext
from ...helpers.types_helper import UsualDict
from ...helpers.db_records.DBRecords import DBRecords

ALL_USER_RECS = None
IGNORE_USER = None

USER_RECEIPT = "receipt"


def fetch_record_s(
    no_sep: str, rec_id: Optional[int] = ALL_USER_RECS, user_id: Optional[int] = IGNORE_USER
) -> Tuple[DBRecords, str, str]:
    """Fetch received files records from the view vw_user_data_files

    no_sep: str: text to show when the record has an empty SEP
    rec_id: int | None: record id to fetch or None
            When rec_id is:
                - ALL_USER_RECS (None), fetch all records for the user with user_id
                - has value, ignore user_id and fetch the record with the given id & return file full_name too
    user_id: int  user id to fetch records for

    return: DBRecords: records fetched and the last record's file full_name

    """

    if rec_id is ALL_USER_RECS and user_id is IGNORE_USER:
        return DBRecords(), "", ""

    file_full_name = ""
    received_recs = ReceivedFiles.get_records(file_id=rec_id, user_id=user_id)
    report_ext = ValidateProcessConfig(False).output_file.ext
    grid_rows: list[UsualDict] = []
    if received_recs:
        """Adapt the records to the local environment"""
        uf = UserFolders()
        user_folder = get_user_folder(user_id) if user_id else app_user.folder  # app_user.folder

        for record in received_recs:
            folder = uf.uploaded if record.file_origin == "L" else uf.downloaded
            file_full_name: str = path.join(folder, user_folder, record.stored_file_name)
            # Copy specific fields to a new object 'row'
            row = {
                "id": record.id,
                "data_f_found": path.isfile(file_full_name),  # data_file was found
                "report_found": path.isfile(change_file_ext(file_full_name, report_ext)),
                "sep": record.sep_fullname if record.sep_fullname else no_sep,
                "file_name": change_file_ext(record.file_name),
                "user_name": record.user_name,
                USER_RECEIPT: record.user_receipt,
                "when": record.submitted_at,
                "errors": record.report_errors,
                "warns": record.report_warns,
            }
            grid_rows.append(row)

    return grid_rows, file_full_name, report_ext


# eof
