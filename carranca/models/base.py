"""
Equipe da Canoa -- 2024

Canoa project declarative base for all SQLAlchemy ORM models.

This class subclasses SQLAlchemy's DeclarativeBase (2.0+ requirement)
and serves as the single shared base for all ORM mappings in the project.


mgd 2026.04.09 -- 20

"""

from typing import TypeVar, Type, List, cast, overload
from dataclasses import is_dataclass
from sqlalchemy import Integer, event, select
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement

from ..helpers.db_helper import db_fetch_rows
from ..common.app_context_vars import sidekick
from ..helpers.db_records.DBRecords import DBRecords

TModel = TypeVar("TModel", bound="CanoaBase")
TRecord = TypeVar("TRecord")


class CanoaBase(DeclarativeBase):
    """Root declarative base for the Canoa project."""

    __read_only__ = False

    def to_dict(self) -> dict:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    @overload
    def get_data(cls: Type[TModel]) -> DBRecords:
        """Return all columns as ORM model instances."""
        ...

    @classmethod
    @overload
    def get_data(cls: Type[TModel], col_names: None) -> DBRecords:
        """Explicit None: return all columns as ORM model instances."""
        ...

    @classmethod
    @overload
    def get_data(cls: Type[TModel], col_names: List[str]) -> DBRecords:
        """List of column names: return specific columns as rows."""
        ...

    @classmethod
    @overload
    def get_data(cls: Type[TModel], col_names: Type[TRecord]) -> DBRecords:
        """Dataclass schema: return dataclass projections."""
        ...

    @classmethod
    def get_data(cls: Type[TModel], col_names: Type[TRecord] | List[str] | None = None) -> DBRecords:
        """
        Typed data factory with flexible column selection.

        Args:
            select_cols: One of:
                - None (default): return all columns as ORM model instances
                - List[str]: specific column names (passed as-is to col_names_to_columns)
                - Type[TRecord] (dataclass): return dataclass projection

        Returns:
            DBRecords wrapping the result rows
        """
        # Determine which columns to select and prepare them for SQL
        selected_cols_names: List[str] = []

        if col_names is None:
            # No selection → select all via ORM model
            selected_cols_names = []
        elif isinstance(col_names, List):
            selected_cols_names = col_names
        elif is_dataclass(schema := col_names):
            fields = schema.__annotations__.keys()
            selected_cols_names = [name for name in fields]
        else:
            raise TypeError(
                f"get_data(sql_select_cols) expects None, List[str], or a dataclass type, "
                f"got {type(col_names).__name__}"
            )

        selected_columns: List[ColumnElement] = [
            col for col in cls.__table__.columns if col.name in selected_cols_names
        ]
        if sidekick.debugging:
            table_col_names = {col.name for col in cls.__table__.columns}
            unknown_cols: List[str] = [col_name for col_name in selected_cols_names if col_name not in table_col_names]
            sidekick.display.error(f"Unknown cols [{', '.join(unknown_cols)}] requested for table {cls.__tablename__}")

        def _get_data(db_session: Session) -> DBRecords:
            stmt = select(*selected_columns) if selected_columns else select(cls)
            rows = db_session.execute(stmt).all()

            return DBRecords(stmt, rows)

        _, _, recs = db_fetch_rows(_get_data, cls.__tablename__)
        return cast(DBRecords, recs)


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
