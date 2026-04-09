"""
Equipe da Canoa -- 2024

Canoa project declarative base for all SQLAlchemy ORM models.

This class subclasses SQLAlchemy's DeclarativeBase (2.0+ requirement)
and serves as the single shared base for all ORM mappings in the project.


mgd 2026.04.09

"""

from typing import List, Type, TypeVar
from sqlalchemy import Integer, event, select
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column

from ..helpers.db_helper import db_fetch_rows, col_names_to_columns
from ..helpers.db_records.DBRecords import DBRecords

TModel = TypeVar("TModel", bound="CanoaBase")


class CanoaBase(DeclarativeBase):
    """Root declarative base for the Canoa project."""

    __read_only__ = False

    def to_dict(self) -> dict:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    def get_data(cls: Type[TModel], col_names: List[str] | None = None) -> DBRecords:
        """
        Returns:
          All records from the table/view represented by `cls`.

        - If `col_names` is provided, only those columns are selected
        - Otherwise, the full mapped model is selected
        """

        col_names = col_names or []

        def _get_data(db_session: Session) -> DBRecords:
            sel_cols = col_names_to_columns(col_names, cls.__table__.columns)

            stmt = select(*sel_cols) if sel_cols else select(cls)
            rows = db_session.execute(stmt).all()

            return DBRecords(stmt, rows)

        _, _, recs = db_fetch_rows(_get_data, cls.__tablename__)
        return recs


class CanoaBaseTable(CanoaBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class CanoaBaseView(CanoaBase):
    __abstract__ = True
    __read_only__ = True  #  👈 can be overridden
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)


@event.listens_for(Session, "before_flush")
def prevent_writes_to_readonly_views(session, flush_context, instances):
    for obj in session.new | session.dirty | session.deleted:
        cls = obj.__class__
        if getattr(cls, "__read_only__", False):
            # TODO Make it nice
            raise RuntimeError(f"Write operation blocked: {cls.__name__} is marked as read-only.")


# eof
