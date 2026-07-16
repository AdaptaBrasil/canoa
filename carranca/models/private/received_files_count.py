"""
 ReceivedFilesCount View

Equipe da Canoa -- 2024

"""

# cSpell:ignore: nullable sqlalchemy

from typing import Optional
from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from ..base import CanoaBaseView
from ...helpers.db_helper import db_fetch_rows
from ...helpers.db_records.DBRecords import DBRecords


class ReceivedFilesCount(CanoaBaseView):
    """
    ReceivedFilesCount is app's interface for the
    DB view `vw_user_data_files_count` that provides the needed
    information to manage users that have send files
    """

    __tablename__ = "vw_user_data_files_count"
    __code_seed__ = 3

    # id: in CanoaBase
    user_name: Mapped[str] = mapped_column(String(100))
    user_email: Mapped[str] = mapped_column(String(100))
    rol_id: Mapped[int] = mapped_column(Integer)
    rol_abbr: Mapped[str] = mapped_column(String(3))
    rol_name: Mapped[str] = mapped_column(String(64))
    files_count: Mapped[int] = mapped_column(Integer)

    @staticmethod
    def get_records(user_id: Optional[int] = None) -> DBRecords:
        def _get_data(db_session: Session) -> DBRecords:
            stmt = select(ReceivedFilesCount)
            if user_id is not None:
                stmt = stmt.where(ReceivedFilesCount.id == user_id)

            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)

            return recs

        _, _, received_files_count = db_fetch_rows(_get_data, ReceivedFilesCount.__tablename__)
        return received_files_count


# eof
