"""
 Private Models
    vw_schema_grid
    view for the Schema Grid

mgd
Equipe da Canoa -- 2025.07.24
"""

# Equipe da Canoa -- 2024
#
# cSpell:ignore: nullable sqlalchemy sessionmaker sep ssep scm sepsusr usrlist SQLA duovigesimal

from sqlalchemy import (
    Computed,
    Boolean,
    Column,
    Integer,
    String,
    select,
)
from sqlalchemy.orm import Session
from typing import List

from ...models import SQLABaseTable
from ...private.IdToCode import IdToCode
from ...helpers.db_helper import db_fetch_rows, col_names_to_columns
from ...helpers.types_helper import OptListOfStr
from ...helpers.db_records.DBRecords import DBRecords


# --- View ---
class SchemaGrid(SQLABaseTable):
    __tablename__ = "vw_schema_grid"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(100))
    color = Column(String(9))
    title = Column(String(140))
    visible = Column(Boolean)
    sep_count = Column(Integer)
    v_sep_count = Column(Integer, Computed(""))  # visible sep
    ui_order = Column(Integer, Computed(""))  # vw_schema_grid is Ordered by this column
    sep_v2t = Column(String(11), Computed(""))  # visible / total

    id_to_code = IdToCode()

    @staticmethod
    def code(id: int) -> str:
        return SchemaGrid.id_to_code.encode(id)

    @staticmethod
    def get_schemas(
        col_names: OptListOfStr = None,
        only_visible: bool | None = None,
    ) -> DBRecords: # List["SchemaGrid"], does not have .to_list()
        """
        Returns:
          All records from SchemaGrid table, optional of selected fields
          If 'only_visible' is True, records are:
            filtered by `visible` = True
            and ordered by 'ui_order'
        """

        def _get_data(db_session: Session):
            sel_cols = col_names_to_columns(col_names, SchemaGrid.__table__.columns)

            stmt = select(*sel_cols) if sel_cols else select(SchemaGrid)
            if only_visible:
                stmt = stmt.where(SchemaGrid.visible == True).order_by(SchemaGrid.ui_order)

            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)
            return recs

        _, _, scm_recs = db_fetch_rows(_get_data, SchemaGrid.__tablename__)
        return scm_recs


# eof
