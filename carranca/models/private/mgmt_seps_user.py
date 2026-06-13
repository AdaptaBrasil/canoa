# cSpell:ignore: nullable sqlalchemy sessionmaker sep ssep scm sepsusr usrlist SQLA duovigesimal

from typing import List, Optional
from datetime import datetime
from sqlalchemy import DateTime, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import CanoaBaseView
from ...helpers.db_records.DBRecords import DBRecords


class MgmtSepsUser(CanoaBaseView):
    __tablename__ = "vw_mgmt_seps_user"
    __read_only__ = False
    __code_seed__ = 9

    # SEP table
    name: Mapped[str] = mapped_column(String(100))
    fullname: Mapped[str] = mapped_column(String(256))  # schema + sep_name
    fullname_lower: Mapped[str] = mapped_column(String(256))
    icon_file_name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(140))
    visible: Mapped[bool] = mapped_column(Boolean)
    # Schema table
    scm_id: Mapped[int] = mapped_column(Integer)
    scm_name: Mapped[str] = mapped_column(String(100))
    # User table
    user_id: Mapped[int] = mapped_column(Integer)
    user_disabled: Mapped[bool] = mapped_column(Boolean)
    user_curr: Mapped[str] = mapped_column(String(100))
    user_new: Mapped[str] = mapped_column(String(100))  #  pass through column: ' '

    spd_id: Mapped[int] = mapped_column(Integer)
    spd_name: Mapped[str] = mapped_column(String(60))

    assigned_at: Mapped[datetime] = mapped_column(DateTime)
    assigned_by: Mapped[int] = mapped_column(Integer)  #  pass through column: 0
    batch_code: Mapped[str] = mapped_column(String(10))  # pass through column: ' '

    @staticmethod
    def _get_user_sep_list(user_id: Optional[int] = None, sep_id: Optional[int] = None) -> DBRecords:
        """⚠️
        any change here must be repeated in
        carranca/private/UserSep.py:UserSep
        """
        field_names = [
            MgmtSepsUser.id.name,
            MgmtSepsUser.name.name,
            MgmtSepsUser.spd_id.name,
            MgmtSepsUser.spd_name.name,
            MgmtSepsUser.scm_name.name,
            MgmtSepsUser.fullname.name,
            MgmtSepsUser.description.name,
            MgmtSepsUser.visible.name,
            MgmtSepsUser.icon_file_name.name,
        ]
        if sep_id is not None:
            field_names.append(MgmtSepsUser.user_curr.name)

        user_sep_list = MgmtSepsUser.get_seps_usr(field_names, user_id, sep_id)
        return user_sep_list

    @staticmethod
    def get_user_sep_list(user_id: int) -> DBRecords:
        """Get seps for one user"""
        return MgmtSepsUser._get_user_sep_list(user_id)

    @staticmethod
    def get_sep_row(sep_id: int) -> Optional["MgmtSepsUser"]:
        """Get one sep"""
        records: DBRecords = MgmtSepsUser._get_user_sep_list(None, sep_id)
        ## 2026-05-15 pythonic: rem return None if records is None or (records.count == 0) else records[0]
        return None if records is None or (len(records) == 0) else records[0]

    @staticmethod
    def get_sep_list() -> DBRecords:
        """Get all seps"""
        return MgmtSepsUser._get_user_sep_list(None, None)

    @staticmethod
    def get_seps_usr(
        col_names: List[str],
        user_id: Optional[int] = None,
        sep_id: Optional[int] = None,
    ) -> DBRecords:
        """
        Returns
        1) `vw_mgmt_seps_user` DB view that has the necessary columns to
            provide the adm with a UI grid to assign or remove SEP
            to or from a user.
        2) Error message if any action fails.
        """
        if user_id is not None:  # then filter
            filter = MgmtSepsUser.user_id == user_id
        elif sep_id is not None:  # then filter
            filter = MgmtSepsUser.id == sep_id
        else:
            filter = 0

        seps_recs = MgmtSepsUser.get_rows(col_names, filter)

        # def _get_data(db_session: Session):
        #     sel_cols = col_names_to_columns(col_names, MgmtSepsUser.__table__.columns)

        #     stmt = select(*sel_cols) if sel_cols else select(MgmtSepsUser)
        #     if user_id is not None:  # then filter
        #         stmt = stmt.where(MgmtSepsUser.user_id == user_id)
        #     if sep_id is not None:  # then filter
        #         stmt = stmt.where(MgmtSepsUser.id == sep_id)

        #     # Sequence[Row[Tuple[MgmtSepsUser]]]
        #     rows: List[Row] = db_session.execute(stmt).all()
        #     recs = DBRecords(stmt, rows)
        #     return recs
        # _, _, seps_recs = db_fetch_rows(_get_data, MgmtSepsUser.__tablename__)
        return seps_recs


# eof
