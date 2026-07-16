"""
 ReceivedFiles View

Equipe da Canoa -- 2024

"""

# cSpell:ignore: nullable sqlalchemy

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session
from ..base import CanoaBaseView
from ...helpers.db_helper import db_fetch_rows
from ...helpers.db_records.DBRecords import DBRecords


class ReceivedFiles(CanoaBaseView):
    """
    ReceivedFiles is app's interface for the
    DB view `vw_user_data_files` that provides the needed
    information to manage the files uploaded by users.
    """

    __tablename__ = "vw_user_data_files"
    __code_seed__ = 4

    # id: in CanoaBase

    user_id: Mapped[int] = mapped_column("id_users", Integer)  # index (user_id, registered_at)
    user_name: Mapped[str] = mapped_column("username", String(100))
    user_email: Mapped[str] = mapped_column("email", String(100))

    # file sep, when registered*
    file_sep_id: Mapped[int] = mapped_column("id_sep", Integer)
    # Sep Id selected by the user to submit the file
    sep_id: Mapped[int] = mapped_column(Integer)
    sep_fullname: Mapped[str] = mapped_column(String(256))

    submitted_at: Mapped[datetime] = mapped_column("registered_at", DateTime)  # index (user_id, registered_at)
    stored_file_name: Mapped[str] = mapped_column(String(180))
    file_name: Mapped[str] = mapped_column("original_name", String(80))
    file_origin: Mapped[str] = mapped_column(String(1))
    file_size: Mapped[int] = mapped_column(Integer)
    file_crc32: Mapped[int] = mapped_column(BigInteger)  # crc32 can exceed int4 range

    report_errors: Mapped[int] = mapped_column(Integer)
    report_warns: Mapped[int] = mapped_column(Integer)

    user_receipt: Mapped[str] = mapped_column(String(15))

    @staticmethod
    def get_records(file_id: int | None, user_id: int | None) -> DBRecords:

        def _get_data(db_session: Session) -> DBRecords:
            # see index user_data_files__id_users__registered_ix
            stmt = select(ReceivedFiles)
            if file_id is not None:
                # For download, one file's id
                stmt = stmt.where(ReceivedFiles.id == file_id)
            elif user_id is not None:
                stmt = stmt.where(ReceivedFiles.user_id == user_id)

            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)

            return recs

        _, _, received_files = db_fetch_rows(_get_data, ReceivedFiles.__tablename__)

        return received_files


# eof
