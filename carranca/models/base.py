"""
Equipe da Canoa -- 2024

Canoa project declarative base for all SQLAlchemy ORM models.

This class subclasses SQLAlchemy's DeclarativeBase (2.0+ requirement)
and serves as the single shared base for all ORM mappings in the project.


mgd 2026.04.09 -- 30

"""

# cspell: words hace

from typing import TypeAlias, Type, List, TypeVar, overload, Optional, cast
from dataclasses import is_dataclass
from sqlalchemy import Integer, ColumnExpressionArgument, event, select
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement

from .. import global_sqlalchemy_scoped_session
from ..private.IdToCode import IdToCode
from ..helpers.db_helper import db_fetch_rows
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import AppStumbled, ModuleErrorCode
from ..helpers.db_records.DBRecords import DBRecords

TModel = TypeVar("TModel", bound="CanoaBase")
TRecord = TypeVar("TRecord")
DBFilter: TypeAlias = ColumnExpressionArgument[bool]


class CanoaBase(DeclarativeBase):
    """Root declarative base for the Canoa project."""

    __code_seed__ = 7  # default, subclasses may override
    __read_only__ = False  # default, subclasses may override

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__id_to_code = IdToCode(cls.__code_seed__)

    # ID Column
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    @classmethod
    def table_name(cls) -> str:
        return cls.__tablename__

    @classmethod
    def to_code(cls: Type[TModel], id: int) -> str:
        return cls.__id_to_code.encode(id)

    @classmethod
    def to_id(cls: Type[TModel], code: str) -> int:
        return cls.__id_to_code.decode(code)

    def to_dict(self) -> dict:
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    def get_row(cls: Type[TModel], id: int) -> TModel | None:
        """Get a single ORM instance by id, for insert/edit operations."""
        with global_sqlalchemy_scoped_session() as db_session:
            try:
                return db_session.get(cls, id)
            except Exception as e:
                db_session.rollback()
                sidekick.display.error(f"Error reading data row from table {cls.table_name}: [{e}].")
                raise Exception(e)

    @classmethod
    def set_row(cls: Type[TModel], row: TModel, return_fresh_row: bool = False) -> TModel | None:
        """
        insert or updates a table record
        """
        db_session: Session
        operation = "inserting" if row.id is None else "updating"
        fresh_row: TModel | None = None
        with global_sqlalchemy_scoped_session() as db_session:
            try:
                db_session.add(row)
                db_session.commit()
                if return_fresh_row:
                    db_session.refresh(row)  # explicit re-fetch
                    fresh_row = row
            except Exception as e:
                db_session.rollback()
                sidekick.display.error(f"Error {operation} data record on table {cls.table_name}: [{e}].")
                raise Exception(e)

        return fresh_row

    @classmethod
    @overload
    def get_rows(
        cls: Type[TModel], col_names: None = None, where_or_id: DBFilter | int = 0, order_col_name: Optional[str] = None
    ) -> DBRecords: ...

    @classmethod
    @overload
    def get_rows(
        cls: Type[TModel], col_names: List[str], where_or_id: DBFilter | int = 0, order_col_name: Optional[str] = None
    ) -> DBRecords: ...

    @classmethod
    @overload
    def get_rows(
        cls: Type[TModel],
        col_names: Type[TRecord],
        where_or_id: DBFilter | int = 0,
        order_col_name: Optional[str] = None,
    ) -> DBRecords: ...

    @classmethod
    def get_rows(
        cls: Type[TModel],
        col_names: Type[TRecord] | List[str] | None = None,
        where_or_id: DBFilter | int = 0,
        order_col_name: Optional[str] = None,
    ) -> DBRecords:
        """
        Typed data factory with flexible column selection, filtering, and ordering.

        Args:
            col_names: One of:
                - None (default): return all columns as ORM model instances
                - Empty(List) = []: return all columns as ORM model instances
                - List[str]: specific column names
                - Type[TRecord] (dataclass): return dataclass projection
            where_or_id: Filter condition:
                - 0 (default): no filtering
                - int: filter by id (WHERE id = where_id)
                - ColumnExpressionArgument[bool]: custom WHERE clause, eg:
                    TModel.spd_id == spd_id
                    TModel.status.in_(["a", "b"])
                    TModel.name.ilike("%foo%")
                    and_(TModel.a == 1, TModel.b == 2)
            order_col: Optional column name to order results by (ORDER BY order_col)

        Returns:
            DBRecords wrapping the result rows
        """

        error_code = ModuleErrorCode.SQLALCHEMY_BASE_TABLE + 1
        error_code += 1

        # Determine which columns to select and prepare them for SQL
        requested_col_names: List[str] = []
        all_cols = False
        order_column: ColumnElement | None = None
        if col_names is None:
            # No selection → select all via ORM model
            all_cols = True
            requested_col_names = []
        elif isinstance(col_names, list):
            requested_col_names = col_names
            all_cols = len(col_names) == 0
        elif is_dataclass(schema := col_names):
            fields = schema.__annotations__.keys()
            requested_col_names = [name for name in fields]
        else:
            raise TypeError(f"get_row() for `col_names` expects  None, List[str], or a dataclass type, " f"got {type(col_names).__name__}")

        error_code += 1
        # Keep the requested order
        # selected_columns: List[ColumnElement] = [
        #     col for col in cls.__table__.columns if all_cols or col.name in selected_cols_names
        # ]
        col_map = {col.name: col for col in cls.__table__.columns}
        selected_columns: List[ColumnElement] = (
            list(cls.__table__.columns) if all_cols else [col_map[name] for name in requested_col_names if name in col_map]
        )

        error_code += 1
        if order_col_name is None:
            pass
        elif not isinstance(order_col_name, str):
            raise TypeError(f"get_row() for `order_col_name` expects None or str, " f"got {type(order_col_name).__name__}")
        elif (order_column := cls.__table__.columns.get(order_col_name)) is None:
            msg = f"Unknown column s [{order_col_name}] requested for table {cls.__tablename__} order by."
            raise AppStumbled(msg, error_code, False, True)

        if sidekick.debugging:
            table_col_names = {col.name for col in cls.__table__.columns}
            unknown_cols: List[str] = [col_name for col_name in requested_col_names if col_name not in table_col_names]
            if unknown_cols:
                raise AppStumbled(
                    f"Unknown cols [{', '.join(unknown_cols)}] requested for table {cls.__tablename__}",
                    error_code,
                    False,
                    True,
                )

        def _get_db_records(db_session: Session) -> DBRecords:
            # Build SELECT statement
            stmt = select(*selected_columns) if selected_columns else select(cls)

            # Apply WHERE filter
            if where_or_id is None:
                pass
            elif not isinstance(where_or_id, int):  # Then is a DBFilter
                where = cast(DBFilter, where_or_id)
                stmt = stmt.where(where)
            elif (id := int(where_or_id)) > 0:  # else if int (can be a false code (see Model.to_id(code))) or Zero (no rows)
                pk = id if id > 0 else 0
                stmt = stmt.where(cls.id == pk)

            # Apply ORDER by
            if order_column is not None:
                stmt = stmt.order_by(order_column)

            rows = db_session.execute(stmt).all()
            return DBRecords(stmt, rows)

        _, _, recs = db_fetch_rows(_get_db_records, cls.__tablename__)
        return cast(DBRecords[TModel], recs)


class CanoaBaseTable(CanoaBase):
    __table_args__ = {"schema": "canoa"}
    __abstract__ = True


class CanoaBaseView(CanoaBase):
    __abstract__ = True
    __read_only__ = True
    # Override id to disable autoincrement for views (y es como se hace):es-PE
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)


@event.listens_for(Session, "before_flush")
def prevent_writes_to_readonly_views(session, flush_context, instances):
    for obj in session.new | session.dirty | session.deleted:
        cls = obj.__class__
        if getattr(cls, "__read_only__", False):
            raise RuntimeError(f"Write operation blocked: {cls.__name__} is marked as read-only.")


# eof
