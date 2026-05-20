# cSpell:ignore: nullable sqlalchemy sessionmaker sep ssep scm sepsusr usrlist SQLA duovigesimal

from typing import List, Optional
from sqlalchemy import DateTime, Boolean, Integer, Column, String, select
from sqlalchemy.orm import Session
from sqlalchemy.engine import Row

from ..base import CanoaBaseView
from ...helpers.db_helper import db_fetch_rows, col_names_to_columns
from ...helpers.db_records.DBRecords import DBRecords
from ...private.IdToCode import IdToCode


class MgmtSepsUser(CanoaBaseView):
    __tablename__ = "vw_mgmt_seps_user"
    __read_only__ = False

    # SEP table
    name = Column(String(100))
    fullname = Column(String(256))  # schema + sep_name
    fullname_lower = Column(String(256))
    icon_file_name = Column(String(120))
    description = Column(String(140))
    visible = Column(Boolean)
    # Schema table
    scm_id = Column(Integer)
    scm_name = Column(String(100))
    # User table
    user_id = Column(Integer)
    user_disabled = Column(Boolean)
    user_curr = Column(String(100))
    user_new = Column(String(100))  #  pass through column: ' '

    assigned_at = Column(DateTime)  # sep.mgmt_users_at
    assigned_by = Column(Integer)  #  pass through column: 0
    batch_code = Column(String(10))  # pass through column: ' '

    # obfuscate the id when is public
    id_to_code = IdToCode()

    @staticmethod
    def code(id: int) -> str:
        """
        Returns an obfuscated code representation of the SEP's internal ID.
        """
        return MgmtSepsUser.id_to_code.encode(id)

    @staticmethod
    def _get_sep_list(user_id: Optional[int] = None, sep_id: Optional[int] = None) -> DBRecords:
        """⚠️
        any change here must be repeated in
        carranca/private/UserSep.py:UserSep
        """
        field_names = [
            MgmtSepsUser.id.name,
            MgmtSepsUser.name.name,
            MgmtSepsUser.scm_id,
            MgmtSepsUser.scm_name.name,
            MgmtSepsUser.fullname.name,
            MgmtSepsUser.description.name,
            MgmtSepsUser.visible.name,
            MgmtSepsUser.icon_file_name.name,
        ]
        if sep_id is not None:
            field_names.append(MgmtSepsUser.user_curr.name)

        return MgmtSepsUser.get_seps_usr(field_names, user_id, sep_id)

    @staticmethod
    def get_user_sep_list(user_id: int) -> DBRecords:
        """Get seps for one user"""
        return MgmtSepsUser._get_sep_list(user_id)

    @staticmethod
    def get_sep_row(sep_id: int) -> Optional["MgmtSepsUser"]:
        """Get one sep"""
        records: DBRecords = MgmtSepsUser._get_sep_list(None, sep_id)
        ## 2026-05-15 pythonic: rem return None if records is None or (records.count == 0) else records[0]
        return None if records is None or (len(records) == 0) else records[0]

    @staticmethod
    def get_sep_list() -> DBRecords:
        """Get all seps"""
        return MgmtSepsUser._get_sep_list(None, None)

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

        def _get_data(db_session: Session):
            # def __cols() -> List[Column]:
            #     all_cols = MgmtSepsUser.__table__.columns
            #     _cols = [col for col in all_cols if col.name in field_names]
            #     return _cols

            # sel_cols = __cols() if field_names else None
            sel_cols = col_names_to_columns(col_names, MgmtSepsUser.__table__.columns)

            stmt = select(*sel_cols) if sel_cols else select(MgmtSepsUser)
            if user_id is not None:  # then filter
                stmt = stmt.where(MgmtSepsUser.user_id == user_id)
            if sep_id is not None:  # then filter
                stmt = stmt.where(MgmtSepsUser.id == sep_id)

            # Sequence[Row[Tuple[MgmtSepsUser]]]
            rows: List[Row] = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)
            return recs

        _, _, seps_recs = db_fetch_rows(_get_data, MgmtSepsUser.__tablename__)
        return seps_recs


# eof
