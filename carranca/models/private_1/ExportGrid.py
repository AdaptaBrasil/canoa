"""
 Private Models
    vw_udf_latest_file
    view with the latest upload file per Sep

mgd
Equipe da Canoa -- 2025.09.02
"""

# Equipe da Canoa -- 2024
#
# cSpell:ignore: nullable sqlalchemy sessionmaker sep ssep scm sepsusr usrlist SQLA duovigesimal

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    select,
    Column,
)
from sqlalchemy.orm import Session

from ...models import SQLABaseTable
from ...helpers.db_helper import db_fetch_rows, col_names_to_columns
from ...helpers.types_helper import OptListOfStr
from ...helpers.db_records.DBRecords import DBRecords


class ExportGrid(SQLABaseTable):
    # Latest user data file by SEP view ()
    __tablename__ = "vw_udf_latest_file"

    id = Column(Integer, primary_key=True)
    sep_id = Column(Integer)
    scm_id = Column(Integer)
    file_name = Column(String(180))
    sep_fullname = Column(String(180))
    uploaded = Column(DateTime)
    report_errors = Column(Integer)

    @staticmethod
    def get_data(
        col_names: OptListOfStr = None,
    ) -> DBRecords:
        """
        Returns:
          All records from SchemaGrid table, optional of selected fields
          If 'only_visible' is True, records are:
            filtered by `visible` = True
            and ordered by 'ui_order'
        """

        def _get_data(db_session: Session):
            sel_cols = col_names_to_columns(col_names, ExportGrid.__table__.columns)

            stmt = select(*sel_cols) if sel_cols else select(ExportGrid)
            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)
            return recs

        _, _, recs = db_fetch_rows(_get_data, ExportGrid.__tablename__)
        return recs


# eof
