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

from sqlalchemy import Computed, Boolean, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from ..base import CanoaBaseView
from ...helpers.db_helper import db_fetch_rows, col_names_to_columns
from ...helpers.types_helper import Opt_List_Of_Str
from ...helpers.db_records.DBRecords import DBRecords


# --- View ---
class SchemaGrid(CanoaBaseView):
    __tablename__ = "vw_schema_grid"
    __code_seed__ = 10

    name: Mapped[str | None] = mapped_column(String(100))
    color: Mapped[str | None] = mapped_column(String(9))
    title: Mapped[str | None] = mapped_column(String(140))
    visible: Mapped[bool | None] = mapped_column(Boolean)
    sep_count: Mapped[int | None] = mapped_column(Integer)
    v_sep_count: Mapped[int | None] = mapped_column(Integer, Computed(""))  # visible sep
    ui_order: Mapped[int | None] = mapped_column(Integer, Computed(""))  # vw_schema_grid is Ordered by this column
    sep_v2t: Mapped[str | None] = mapped_column(String(11), Computed(""))  # visible / total

    # TODO refactor to self.get_data()
    @staticmethod
    def get_schemas(
        col_names: Opt_List_Of_Str = None,
        only_visible: bool | None = None,
    ) -> DBRecords:  # List["SchemaGrid"], does not have .to_list()
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
