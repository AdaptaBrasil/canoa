"""
 Schema Table

Equipe da Canoa -- 2024

"""

# cSpell:ignore: nullable sqlalchemy

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, select, text
from sqlalchemy.orm import Mapped, mapped_column, Session
from ... import global_sqlalchemy_scoped_session
from ..base import CanoaBaseTable
from ...helpers.db_helper import db_fetch_rows, col_names_to_columns
from ...helpers.types_helper import Opt_List_Of_Str
from ...common.app_context_vars import sidekick
from ...helpers.db_records.DBRecords import DBRecords


class Schema(CanoaBaseTable):
    __tablename__ = "schema"
    __code_seed__ = 8

    # id: in CanoaBase
    # del_at, del_by: soft-delete columns, DB-trigger managed, not mapped here
    name: Mapped[str | None] = mapped_column(String(100))
    color: Mapped[str | None] = mapped_column(String(9))
    title: Mapped[str | None] = mapped_column(String(140))
    description: Mapped[str | None] = mapped_column(String(140))
    content: Mapped[str | None] = mapped_column(Text)
    visible: Mapped[bool | None] = mapped_column(Boolean)
    ui_order: Mapped[int | None] = mapped_column(Integer)
    ins_by: Mapped[int | None] = mapped_column(Integer)
    ins_at: Mapped[datetime | None] = mapped_column(DateTime)
    edt_by: Mapped[int | None] = mapped_column(Integer)
    edt_at: Mapped[datetime | None] = mapped_column(DateTime)

    @staticmethod
    def get_row(id: int) -> "Schema":

        def _get_data(db_session: Session):
            stmt = select(Schema).where(Schema.id == id)
            scm_row = db_session.execute(stmt).scalar_one_or_none()
            if scm_row is not None:
                scm_row.color = scm_row.color.strip()
                # TODO
                # ALTER TABLE canoa."schema"
                # ALTER COLUMN color TYPE VARCHAR(9) USING RTRIM(color);
            return scm_row

        _, _, row = db_fetch_rows(_get_data, Schema.__tablename__)
        return row

    @staticmethod
    def get_schemas(col_names: Opt_List_Of_Str = None, order_by: str = "") -> DBRecords:
        """
        Returns:
          All records from Schema table, optional of selected fields, order by the order_by, eg 'name ASC'
        """

        def _get_data(db_session: Session):
            sel_cols = col_names_to_columns(col_names, Schema.__table__.columns)

            stmt = select(*sel_cols) if sel_cols else select(Schema)
            if order_by:
                stmt = stmt.order_by(text(order_by))

            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)
            return recs

        _, _, scm_recs = db_fetch_rows(_get_data, Schema.__tablename__)
        return scm_recs

    @staticmethod
    def save(sep_row: "Schema"):
        """
        Saves a Schema record
        """

        db_session: Session
        with global_sqlalchemy_scoped_session() as db_session:
            try:
                db_session.add(sep_row)
                db_session.commit()

            except Exception as e:
                db_session.rollback()
                sidekick.display.error(f"Error saving Schema record: [{e}].")
                raise Exception(e)

        return


# eof
