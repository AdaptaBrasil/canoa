"""
 Private Models
    vw_export_files
    view with the user files to export

mgd
Equipe da Canoa -- 2025.09.02
"""

# Equipe da Canoa -- 2025
#
# cSpell:ignore: 

from sqlalchemy import DateTime, Integer, String, Column
from sqlalchemy.orm import Session

from ..base import CanoaBaseTable


class ExportGrid(CanoaBaseTable):
    # Latest user data file by SEP view ()
    __tablename__ = "vw_export_data_files"

    user_id = Column(Integer)
    sep_id = Column(Integer)
    scm_id = Column(Integer)
    file_origin = Column(String(1))
    file_name = Column(String(180))
    sep_fullname = Column(String(180))
    uploaded = Column(DateTime)
    report_errors = Column(Integer)

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
