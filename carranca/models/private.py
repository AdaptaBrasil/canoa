"""
 Private Models

mgd
Equipe da Canoa -- 2024
"""

# cSpell:ignore: nullable sqlalchemy sessionmaker sep ssep scm sepsusr usrlist SQLA duovigesimal

from typing import List, Optional
from ..public.ups_handler import AppStumbled
from ..private.scm_export_ui_save import SepUiOrder
from sqlalchemy import (
    Computed,
    DateTime,
    Boolean,
    Integer,
    Column,
    String,
    select,
    exists,
    Text,
    text,
    func,
    and_,
)
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import defer, Session
from sqlalchemy.ext.hybrid import hybrid_property

from .. import global_sqlalchemy_scoped_session

from ..models import SQLABaseTable
from ..helpers.db_helper import db_fetch_rows, col_names_to_columns
from ..helpers.py_helper import is_str_none_or_empty
from ..helpers.user_helper import get_user_code
from ..helpers.types_helper import OptListOfStr
from ..private.SepIconMaker import SepIconMaker, SvgContent
from ..common.app_context_vars import sidekick, app_user
from ..helpers.db_records.DBRecords import DBRecords

from ..private.IdToCode import IdToCode


# --- Table ---
class UserDataFiles(SQLABaseTable):
    """
    UserDataFiles is app's interface for the
    DB table `user_data_files` that works as a
    log of the validation process. Every step
    of the process (that starts with
    uploading a file and ends with sending an
    email with the validation report attached
    or displaying a error message)
    is recorded in one row.
    """

    __tablename__ = "user_data_files"

    # register, pk/fk/uniqueKey
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket = Column(String(40), unique=True)
    id_sep = Column(Integer)  # fk
    id_users = Column(Integer)  # fk
    log_file_name = Column(String(200))  # use in case of error
    # register, file info
    file_name = Column(String(80))
    file_size = Column(Integer)
    file_crc32 = Column(Integer)
    user_receipt = Column(String(14))

    # register, sys info
    db_version = Column(String(12))
    app_version = Column(String(12))
    process_version = Column(String(12))

    from_os = Column(String(1))
    file_origin = Column(String(1))
    original_name = Column(String(80), nullable=True, default=None)

    ## register
    a_received_at = Column(DateTime)
    b_process_started_at = Column(DateTime)
    c_check_started_at = Column(DateTime)
    d_register_started_at = Column(DateTime)

    ## submit & email & process
    e_unzip_started_at = Column(DateTime)
    f_submit_started_at = Column(DateTime)
    g_report_ready_at = Column(DateTime)

    ## submit
    validator_version = Column(String(8))
    validator_result = Column(String(280))
    report_errors = Column(Integer)
    report_warns = Column(Integer)
    report_tests = Column(Integer)

    ## submit & email
    h_email_started_at = Column(DateTime)

    ## email.py
    email_sent = Column(Boolean, default=False)

    ## process, on exit
    error_code = Column(Integer, nullable=True)
    error_msg = Column(String(200), nullable=True)
    error_text = Column(Text, nullable=True)
    success_text = Column(Text, nullable=True)
    z_process_end_at = Column(DateTime)

    ## Set on trigger
    # registered_at, at insert
    # db_version
    # email_sent_at, when email_sent = T
    # error_at, at error_code not 0
    # Special
    # error_handled, when admin handles the error (TODO)

    ## obsolete
    # upload_start_at ->
    # report_ready_ay -> g_report_ready_at
    #

    # Helpers
    @staticmethod
    def _get_record(db_session: Session, uTicket: str):
        """gets the record with unique key: uTicket"""
        stmt = select(UserDataFiles).where(UserDataFiles.ticket == uTicket)
        rows = db_session.scalars(stmt).all()
        if not rows:
            return None
        elif len(rows) == 1:
            return rows[0]
        else:
            raise KeyError(f"The ticket {uTicket} return several records, expecting only one.")

    @staticmethod
    def _ins_or_upd(isInsert: bool, uTicket: str, **kwargs) -> None:
        """insert or update a record with unique key: uTicket"""
        # action: insert/update
        isUpdate = not isInsert
        db_session: Session
        with global_sqlalchemy_scoped_session() as db_session:
            try:
                # if update, fetch existing record
                # if insert, check if record already exists
                record_to_ins_or_upd = UserDataFiles._get_record(db_session, uTicket)
                # check invalid conditions
                msg_exists = f"The ticket '{uTicket}' is " + "{0} registered."
                if isUpdate and record_to_ins_or_upd is None:
                    raise KeyError(msg_exists.format("not"))
                elif isInsert and record_to_ins_or_upd is not None:
                    raise KeyError(msg_exists.format("already"))
                elif isInsert:
                    record_to_ins_or_upd = UserDataFiles(ticket=uTicket, **kwargs)
                    db_session.add(record_to_ins_or_upd)
                else:  # isUpdate
                    for attr, value in kwargs.items():
                        if value is not None:
                            setattr(record_to_ins_or_upd, attr, value)

                db_session.commit()

            except Exception as e:
                db_session.rollback()
                operation = "update" if isUpdate else "insert to"
                msg_error = f"Cannot {operation} {UserDataFiles.__tablename__}.ticket = {uTicket} | Error {e}."
                sidekick.app_log.error(msg_error)
                raise DatabaseError(msg_error)
        return None

    # Public insert/update
    def insert(uTicket: str, **kwargs) -> None:
        UserDataFiles._ins_or_upd(True, uTicket, **kwargs)
        return None

    def update(uTicket: str, **kwargs) -> None:
        UserDataFiles._ins_or_upd(False, uTicket, **kwargs)
        return None


# --- Table ---
class Schema(SQLABaseTable):
    __tablename__ = "schema"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    color = Column(String(9))
    title = Column(String(140))
    description = Column(String(140))
    content = Column(Text)
    visible = Column(Boolean)
    ui_order = Column(Integer)
    ins_by = Column(Integer)
    ins_at = Column(DateTime)
    edt_by = Column(Integer)
    edt_at = Column(DateTime)

    # obfuscate the id when is public
    id_to_code = IdToCode()

    @staticmethod
    def to_id(code: str) -> int:
        return Schema.id_to_code.decode(code)

    @hybrid_property
    def code(self):
        """
        Returns an obfuscated user's id.
        """
        return Schema.id_to_code.encode(self.user_id)

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
    def get_schemas(col_names: OptListOfStr = None, order_by: str = "") -> DBRecords:
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


# --- Table ---
class MgmtEmailSep(SQLABaseTable):
    """
    This *Updatable view `vw_mgmt_email_sep` exposes
    columns to assist in sending emails to users when
    the SEP assigned to them is changed by an admin.
        ./private/sep_mgmt/send_email.py
        updates email_at and email_error
    """

    __tablename__ = "vw_mgmt_email_sep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    new_user_name = Column(String, Computed(""))  # read only columns
    new_user_email = Column(String, Computed(""))
    old_user_name = Column(String, Computed(""))
    old_user_email = Column(String, Computed(""))
    sep_fullname = Column(String, Computed(""))
    batch_code = Column(String(10))
    email_at = Column(DateTime)
    email_error = Column(String(400))


# --- Table ---
class Sep(SQLABaseTable):
    """
    Table `sep` keeps the basic information of
    each SEP
    """

    __tablename__ = "sep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_schema = Column(Integer)
    users_id = Column("mgmt_users_id", Integer)
    ui_order = Column(Integer)
    ins_by = Column(Integer)
    ins_at = Column(DateTime)
    edt_by = Column(Integer)
    edt_at = Column(DateTime)
    ico_by = Column(Integer)
    ico_at = Column(DateTime)
    name = Column(String(100), unique=True, nullable=False)
    name_lower = Column(String(100), Computed(""), unique=True)
    description = Column(String(140), nullable=False)
    visible = Column(Boolean)
    icon_file_name = Column(String(120), nullable=True)
    icon_uploaded_at = Column(DateTime, nullable=True)
    icon_version = Column(Integer, nullable=False)
    icon_original_name = Column(String(120))
    icon_svg = Column(Text)
    icon_crc = Column(Integer)

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
    def get_content(id: int) -> Optional[SvgContent]:
        """
        Returns the content of the icon_svg (useful for creating a file)
        """

        def _get_data(db_session: Session) -> SvgContent:
            try:
                stmt = select(Sep).where(Sep.id == id)
                sep = db_session.execute(stmt).scalar_one_or_none()
                is_empty = is_str_none_or_empty(sep.icon_svg)
                icon_content = SepIconMaker.empty_content if is_empty else sep.icon_svg
            except Exception as e:
                icon_content = SepIconMaker.error_content
                sidekick.app_log.error(f"Error retrieving icon content of SEP {id}: [{e}].")
            return icon_content

        e, msg_error, icon_content = db_fetch_rows(_get_data)
        return icon_content, msg_error

    @staticmethod
    def save_ui_order(items: SepUiOrder, task_code: int) -> bool:
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
                raise AppStumbled("Error save Schema ui-order.", task_code, False, e)

        return True

    @staticmethod
    def save(sep_row: "Sep", schema_changed: bool, batch_code: str) -> int:
        """
        Saves a Sep record
            if OK -> returns the row id
            else -> -1
        """

        def _log(operation: str):
            log_row = LogUserSep()
            log_row.id_sep = sep_row.id
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

                sep_id = sep_row.id
                db_session.commit()

            except Exception as e:
                db_session.rollback()
                sidekick.display.error(f"Error saving SEP record: [{e}].")

        return sep_id

    @staticmethod
    def full_name_exists(id_schema: int, sep_name: str) -> bool:

        def _get_data(db_session: Session) -> SvgContent:
            # see sep__sch_name_lower_uix
            stmt = select(Sep.name_lower).where(Sep.id_schema == id_schema, Sep.name_lower == func.lower(sep_name))
            name_exists = db_session.query(exists(stmt)).scalar()
            return name_exists

        _, _, name_exists = db_fetch_rows(_get_data, Sep.__tablename__)
        return name_exists

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


# --- View ---
class ReceivedFiles(SQLABaseTable):
    """
    ReceivedFiles is app's interface for the
    DB view `vw_user_data_files` that provides the needed
    information to manage the files uploaded by users.
    """

    __tablename__ = "vw_user_data_files"

    id = Column(Integer, primary_key=True)
    user_id = Column("id_users", Integer)  # index (user_id, registered_at)
    user_name = Column("username", String(100))
    user_email = Column("email", String(100))

    # file sep, when registered*
    file_sep_id = Column("id_sep", Integer)
    # Sep Id selected by the user to submit the file
    sep_id = Column(Integer)
    sep_fullname = Column(String(256))

    submitted_at = Column("registered_at", DateTime)  # index (user_id, registered_at)
    stored_file_name = Column(String(180))
    file_name = Column("original_name", String(80))
    file_origin = Column(String(1))
    file_size = Column(Integer)
    file_crc32 = Column(Integer)

    report_errors = Column(Integer)
    report_warns = Column(Integer)

    user_receipt = Column(String(15))
    email_sent = Column(Boolean)  # index (email_sent, had_reception_error, user_id, registered_at)
    had_reception_error = Column(Boolean)  # index (email_sent, had_reception_error, user_id, registered_at)

    @staticmethod
    def get_records(
        file_id: int,
        user_id: int,
        email_sent: bool = True,
        had_reception_error: bool = False,
    ) -> DBRecords:

        def _get_data(db_session: Session) -> DBRecords:
            """
            ----------------------------------------------
            | ⚠️ Attention
            -------------------------------------------------
                There is an index on the underlying table
                (email_sent, had_reception_error, user_id, registered_at)
                so if you are going change the where clause, be sure
                to include these fields.
            """
            stmt = select(ReceivedFiles)
            if file_id is not None:
                # For download, one file's id
                stmt = stmt.where(ReceivedFiles.id == file_id)
            else:
                # For grid
                stmt = stmt.where(
                    # 2025.11.11 debuging ReceivedFiles.had_reception_error == had_reception_error,
                    # and_( # and_(  mgd-bug-2025-10-01
                    #     ReceivedFiles.email_sent == email_sent,
                    #     ReceivedFiles.had_reception_error == had_reception_error,
                    # )
                )
                if user_id is not None:
                    stmt = stmt.where(ReceivedFiles.user_id == user_id)

            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)

            return recs

        _, _, received_files = db_fetch_rows(_get_data, ReceivedFiles.__tablename__)

        return received_files


# --- Table ---
class ReceivedFilesCount(SQLABaseTable):
    """
    ReceivedFilesCount is app's interface for the
    DB view `vw_user_data_files_count` that provides the needed
    information to manage users that have send files
    """

    __tablename__ = "vw_user_data_files_count"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(100))
    user_email = Column(String(100))
    rol_id = Column(Integer)
    rol_abbr = Column(String(3))
    rol_name = Column(String(64))
    files_count = Column(Integer)

    @hybrid_property
    def user_code(self):
        return get_user_code(self.user_id)

    @staticmethod
    def get_records(user_id: Optional[int] = None) -> DBRecords:
        def _get_data(db_session: Session) -> DBRecords:
            stmt = select(ReceivedFilesCount)
            if user_id is not None:
                stmt = stmt.where(ReceivedFilesCount.user_id == user_id)

            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)

            return recs

        _, _, received_files_count = db_fetch_rows(_get_data, ReceivedFilesCount.__tablename__)
        return received_files_count


# --- Table ---
class LogUserSep(SQLABaseTable):
    """
    Keeps track of SEP management user (actual and last one)
    and
    insert and editions to table Sep
    """

    __tablename__ = "log_user_sep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_sep = Column(Integer, nullable=False)
    # Set NULL when remove sep from user (=id_users_prior)
    id_users = Column(Integer, nullable=True)
    # The user ID of the previous owner of the SEP, or None if none was assigned
    id_users_prior = Column(Integer, nullable=True)
    done_at = Column(DateTime, nullable=False, default=func.now())
    done_by = Column(Integer, nullable=False)  # The new SEP owner user id
    # (days since 2024.11.01).(ms) both in base duovigesimal (22)
    batch_code = Column(String(10), nullable=False)
    email_at = Column(DateTime, nullable=True)
    email_error = Column(String(800), nullable=True)
    # (S)et, (Removed | (Edited, marked as (Deleted | (Change schema. For insert, see sep.ins_at.
    operation = Column(String(1), nullable=True)


class MgmtSepsUser(SQLABaseTable):
    __tablename__ = "vw_mgmt_seps_user"

    # SEP table
    id = Column(Integer, primary_key=True, autoincrement=False)  # like a PK
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
        return None if records is None or (records.count == 0) else records[0]

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

            rows = db_session.execute(stmt).all()
            recs = DBRecords(stmt, rows)
            return recs

        _, _, seps_recs = db_fetch_rows(_get_data, MgmtSepsUser.__tablename__)
        return seps_recs


# eof
