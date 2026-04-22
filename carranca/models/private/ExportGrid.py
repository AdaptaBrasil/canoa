"""
 Private Models
    vw_export_files
    view with the user files to export

mgd
Equipe da Canoa -- 2025.09.02
"""

# Equipe da Canoa -- 2025

from datetime import datetime
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import CanoaBaseTable


class ExportGrid(CanoaBaseTable):
    # Latest user data file by SEP view ()
    __tablename__ = "vw_export_data_files"

    user_id: Mapped[int] = mapped_column(Integer)
    sep_id: Mapped[int] = mapped_column(Integer)
    scm_id: Mapped[int] = mapped_column(Integer)

    file_origin: Mapped[str] = mapped_column(String(1))
    file_name: Mapped[str] = mapped_column(String(180))
    sep_fullname: Mapped[str] = mapped_column(String(180))

    uploaded: Mapped[datetime] = mapped_column(DateTime)
    report_errors: Mapped[int] = mapped_column(Integer)

    # @staticmethod
    # def get_data(
    #     col_names: List[str] = [],
    # ) -> DBRecords:
    #     """
    #     Returns:
    #       All records from SchemaGrid table, optional of selected fields
    #       If 'only_visible' is True, records are:
    #         filtered by `visible` = True
    #         and ordered by 'ui_order'
    #     """

    #     def _get_data(db_session: Session):
    #         sel_cols = col_names_to_columns(col_names, ExportGrid.__table__.columns)

    #         stmt = select(*sel_cols) if sel_cols else select(ExportGrid)
    #         rows = db_session.execute(stmt).all()
    #         recs = DBRecords(stmt, rows)
    #         return recs

    #     _, _, recs = db_fetch_rows(_get_data, ExportGrid.__tablename__)
    #     return recs


# eof
