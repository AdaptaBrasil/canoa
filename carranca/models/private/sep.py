"""
 Sep Table

Equipe da Canoa -- 2024

"""

# cSpell:ignore: nullable sqlalchemy sep ssep scm

from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, Computed, DateTime, Integer, String, Text, and_, exists, func, select
from sqlalchemy.orm import Mapped, Session, defer, mapped_column

from ..base import CanoaBaseTable
from .log_user_sep import LogUserSep
from ... import global_sqlalchemy_scoped_session
from ...common.app_context_vars import app_user, sidekick
from ...helpers.db_helper import col_names_to_columns, db_fetch_rows
from ...helpers.db_records.DBRecords import DBRecords
from ...helpers.py_helper import is_str_none_or_empty
from ...private.scm_export_ui_save import Sep_UI_Order
from ...private.SepIconMaker import SepIconMaker, Svg_Content
from ...public.ups_handler import AppStumbled


class Sep(CanoaBaseTable):
    """
    Table `sep` keeps the basic information of
    each SEP
    """

    __tablename__ = "sep"
    __code_seed__ = 11

    # id: in CanoaBase
    # del_at, del_by: soft-delete columns, DB-trigger managed, not mapped here
    # mgmt_users_at, mgmt_batch_code: DB-trigger managed (vw_mgmt_seps_user__on_upd), exposed via MgmtSepsUser.assigned_at/batch_code instead
    id_schema: Mapped[int | None] = mapped_column(Integer)
    id_spd: Mapped[int | None] = mapped_column(Integer)  # FK to SPatial_Data_files
    users_id: Mapped[int | None] = mapped_column("mgmt_users_id", Integer)
    ui_order: Mapped[int | None] = mapped_column(Integer)
    ins_by: Mapped[int | None] = mapped_column(Integer)
    ins_at: Mapped[datetime | None] = mapped_column(DateTime)
    edt_by: Mapped[int | None] = mapped_column(Integer)
    edt_at: Mapped[datetime | None] = mapped_column(DateTime)
    ico_by: Mapped[int | None] = mapped_column(Integer)
    ico_at: Mapped[datetime | None] = mapped_column(DateTime)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_lower: Mapped[str | None] = mapped_column(String(100), Computed(""), unique=True)
    description: Mapped[str] = mapped_column(String(140), nullable=False)
    visible: Mapped[bool | None] = mapped_column(Boolean)
    icon_file_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    icon_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    icon_version: Mapped[int] = mapped_column(Integer, nullable=False)
    icon_original_name: Mapped[str | None] = mapped_column(String(120))
    icon_svg: Mapped[str | None] = mapped_column(Text)
    icon_crc: Mapped[int | None] = mapped_column(BigInteger)  # crc32 can exceed int4 range

    # const
    scm_sep = sidekick.config.SCM_SEP_SEPARATOR

    @staticmethod
    def get_fullname(scm_name: str, sep_name: str) -> str:
        return f"{scm_name}{Sep.scm_sep}{sep_name}"

    @staticmethod
    def get_row(id: int, load_icon: Optional[bool] = False) -> "Sep":
        """
        Select a SEP by id, with deferred Icon content (useful for edition). It also
        returns the SEP's full name (schema/SEP) (config.SCM_SEP_SEPARATOR) the view `vw_scm_sep`.

        NB:
            Forward Reference
            Optional['MgmtSep']
            using quotes around a type in type hints is known as a forward reference.
        """
        if id is None:
            return None

        def _get_data(db_session: Session) -> Sep:
            stmt = select(Sep).options(defer(Sep.icon_svg)).where(Sep.id == id)
            sep_row = db_session.execute(stmt).scalar_one_or_none()

            if sep_row and load_icon:
                db_session.refresh(sep_row, attribute_names=[Sep.icon_svg.name])

            return sep_row

        _, _, sep_row = db_fetch_rows(_get_data, Sep.__tablename__)
        return sep_row

    @staticmethod
    def get_content(id: int) -> tuple[Svg_Content, Optional[str]]:
        """
        Returns the content of the icon_svg (useful for creating a file)
        """

        def _get_data(db_session: Session) -> Svg_Content:
            try:
                stmt = select(Sep).where(Sep.id == id)
                sep = db_session.execute(stmt).scalar_one_or_none()
                is_empty = is_str_none_or_empty(sep.icon_svg)
                icon_content = SepIconMaker.empty_content() if is_empty else sep.icon_svg
            except Exception as e:
                icon_content = SepIconMaker.error_content()
                sidekick.display.error(f"Error retrieving icon content of SEP {id}: [{e}].")
            return icon_content

        e, msg_error, icon_content = db_fetch_rows(_get_data)
        return icon_content, msg_error

    @staticmethod
    def save_ui_order(items: Sep_UI_Order, task_code: int) -> bool:
        # The new order is implied by the position in the list, grouped by schema.
        # ⚠️ We intentionally update *all* items instead of only modified ones.
        #     Reason: keeping the stored order always synchronized with the frontend
        #     ensures deterministic behavior, avoids "out-of-sync" inconsistencies,
        #     and greatly simplifies rollback and debugging.
        #     The performance cost is negligible given the small number of SEPs per SCM.

        db_session: Session
        sep_id = -1
        with global_sqlalchemy_scoped_session() as db_session:
            try:
                for sep_id, new_index in items:
                    db_session.query(Sep).filter_by(id=sep_id).update({"ui_order": new_index})

                db_session.commit()

            except Exception as e:
                db_session.rollback()
                raise AppStumbled("Error saving Schema's ui-order.", task_code, False, e)

        return True

    @staticmethod
    def save(sep_row: "Sep", schema_changed: bool, visible_changed: bool, batch_code: str) -> int:
        """
        Saves a Sep record
            if OK -> returns the row id
            else -> -1
        """

        def _log(operation: str):
            log_row = LogUserSep()
            log_row.id_sep = sep_row.id
            log_row.id_users = sep_row.users_id  # the SEP's manager at the time of this operation
            log_row.done_by = app_user.id
            log_row.operation = operation
            log_row.batch_code = batch_code
            return log_row

        db_session: Session
        sep_id = -1
        with global_sqlalchemy_scoped_session() as db_session:
            try:
                db_session.add(sep_row)
                if sep_row.id is None:  # is it an insert?
                    db_session.flush()  # get sep_row.id
                    db_session.add(_log("I"))
                else:
                    db_session.add(_log("E"))
                    if schema_changed:
                        db_session.add(_log("C"))
                    if visible_changed:
                        db_session.add(_log("X" if sep_row.visible else "F"))

                sep_id = sep_row.id
                db_session.commit()

            except Exception as e:
                db_session.rollback()
                sidekick.display.error(f"Error saving SEP record: [{e}].")

        return sep_id

    @staticmethod
    def full_name_exists(id_schema: int, sep_name: str) -> bool:

        def _get_data(db_session: Session) -> Svg_Content:
            # see sep__sch_name_lower_uix
            stmt = select(Sep.name_lower).where(Sep.id_schema == id_schema, Sep.name_lower == func.lower(sep_name))
            name_exists = db_session.query(exists(stmt)).scalar()
            return name_exists

        _, _, name_exists = db_fetch_rows(_get_data, Sep.__tablename__)
        return name_exists

    @staticmethod
    def icon_exist_sep(sep_id: int, icon_crc: int) -> str:

        def _get_data(db_session: Session) -> str:
            stmt = select(Sep.name).where(Sep.id != sep_id, Sep.icon_crc == icon_crc)
            sep_name = db_session.execute(stmt).scalar()
            return sep_name

        _, _, sep_name = db_fetch_rows(_get_data, Sep.__tablename__)
        return sep_name

    @staticmethod
    def get_visible_seps_of_scm(scm_id: int, col_names: List[str]) -> List["Sep"]:
        if id is scm_id:
            return None

        def _get_data(db_session: Session) -> List[Sep]:
            sel_cols = col_names_to_columns(col_names, Sep.__table__.columns)
            stmt = select(*sel_cols).where(and_(Sep.id_schema == scm_id, Sep.visible == True)).order_by(Sep.ui_order)
            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)
            return recs

        _, _, sep_rows = db_fetch_rows(_get_data, Sep.__tablename__)
        return sep_rows


# eof
