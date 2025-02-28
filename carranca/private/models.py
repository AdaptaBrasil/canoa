"""
    Model of the table of files uploaded by users

    mgd
    Equipe da Canoa -- 2024
"""

# cSpell:ignore ssep

# Equipe da Canoa -- 2024
#
# cSpell:ignore: nullable psycopg2 sqlalchemy sessionmaker mgmt

from typing import Optional, Tuple
from psycopg2 import DatabaseError, OperationalError
from sqlalchemy import and_, select
from sqlalchemy import Boolean, Column, Computed, DateTime, Integer, String, Text
from sqlalchemy.orm import defer, Session as SQLAlchemySession, declarative_base

from carranca import SqlAlchemyScopedSession

from .SepIconConfig import SepIconConfig, SvgContent
from ..common.app_context_vars import sidekick
from ..helpers.db_helper import DBRecords
from ..helpers.py_helper import is_str_none_or_empty

# https://stackoverflow.com/questions/45259764/how-to-create-a-single-table-using-sqlalchemy-declarative-base
Base = declarative_base()


# --- Table ---
class UserDataFiles(Base):
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
    def _get_record(session: SQLAlchemySession, uTicket: str):
        """gets the record with unique key: uTicket"""
        stmt = select(UserDataFiles).where(UserDataFiles.ticket == uTicket)
        rows = session.scalars(stmt).all()
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
        with SqlAlchemyScopedSession() as db_session:
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
                msg_error = (
                    f"Cannot {operation} {UserDataFiles.__tablename__}.ticket = {uTicket} | Error {e}."
                )
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
class MgmtUserSep(Base):
    """
    `vw_mgmt_user_sep` is DB view which holds the necessary information
    to provide the app's admin a UI grid so the admin can assign or remove
    SEP to or from a user.

    The view has a trigger that saves the information on `users` table and
    logs the action on `log_user_sep` table.
    """

    __tablename__ = "vw_mgmt_user_sep"

    # https://docs.sqlalchemy.org/en/13/core/type_basics.html
    user_id = Column(Integer, primary_key=True, autoincrement=False)  # like a PK
    sep_id = Column(Integer)
    user_name = Column(String(100))
    disabled = Column("user_disabled", Boolean)
    scm_sep_curr = Column(String(201))  # sep_name -> scm_sep_curr
    scm_sep_new = Column(String(201))  # sep_new -> scm_sep_new
    when = Column("assigned_at", DateTime)
    assigned_by = Column(Integer)
    batch_code = Column(String(10))  # trace_code

    @staticmethod
    def get_grid_view() -> Tuple[DBRecords, DBRecords, str]:
        """
        Returns
        1) `vw_mgmt_user_sep` DB view that has the necessary columns to
            provide the user with a UI grid to assign or remove SEP
            to or from a user.
        2) `vw_scm_sep` SEP list.
        3) Error message if any action fails.
        """

        users_sep: DBRecords = None
        sep_list: DBRecords = None
        msg_error = None
        with SqlAlchemyScopedSession() as db_session:
            try:
                mus_recs = db_session.scalars(select(MgmtUserSep)).all()
                users_sep = DBRecords(MgmtUserSep.__tablename__, mus_recs)

                ssep_recs = db_session.scalars(select(SchemaSEP)).all()
                sep_list = DBRecords(SchemaSEP.__tablename__, ssep_recs)

            except Exception as e:
                msg_error = str(e)
                sidekick.display.error(msg_error)

        return users_sep, sep_list, msg_error


# --- Table ---
class MgmtEmailSep(Base):
    """
    This read only DB view `view vw_mgmt_email_sep` exposes
    columns to assist sending emails to users when their SEP
    attribute is changed by an admin.
    """

    __tablename__ = "vw_mgmt_email_sep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, Computed(""))
    user_name = Column(String, Computed(""))
    user_email = Column(String, Computed(""))
    sep_name_new = Column(String, Computed(""))
    sep_name_old = Column(String, Computed(""))
    email_at = Column(DateTime)
    email_error = Column(String(400))
    batch_code = Column(String(10), Computed(""))


# --- Table ---
class SchemaSEP(Base):
    """
    SchemaSEP is app's interface for the
    DB view `vw_scm_sep` that provides a couple of
    columns .
    """

    __tablename__ = "vw_scm_sep"
    id = Column("sep_id", Integer, primary_key=True)
    sep_fullname = Column(Text)


# --- Table ---
class MgmtSep(Base):
    """
    Table `sep` keeps the basic information of
    each SEP
    """

    __tablename__ = "sep"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(140), nullable=False)
    icon_file_name = Column(String(120), nullable=True)
    icon_uploaded_at = Column(DateTime, nullable=True)
    icon_original_name = Column(String(120), nullable=True)
    icon_svg = Column(Text, nullable=True)

    @staticmethod
    def get_sep(id: int) -> Tuple[Optional["MgmtSep"], str]:
        """
        Select a SEP by id, with deferred Icon content (useful for edition). It also
        returns the SEP's full name (schema + SEP) from the view `vw_scm_sep`.

        NB:
            Forward Reference
            Optional['MgmtSep']
            using quotes around a type in type hints is known as a forward reference.
        """
        if id is None:
            return None, None

        sep: Optional[MgmtSep] = None
        sep_fullname: Optional[str] = None
        with SqlAlchemyScopedSession() as db_session:
            try:
                stmt = select(MgmtSep).options(defer(MgmtSep.icon_svg)).where(MgmtSep.id == id)
                _sep = db_session.execute(stmt).scalar_one_or_none()
                stmt = select(SchemaSEP).where(SchemaSEP.id == _sep.id)
                row = db_session.execute(stmt).one_or_none()
                sep_fullname = None if row is None else row[0].sep_fullname
                sep = _sep
            except (OperationalError, DatabaseError) as e:
                sidekick.app_log.error(f"Database connection error: {e}")
            except Exception as e:
                sidekick.app_log.error(f"Error fetching user SEP info: {e}")

        return sep, sep_fullname

    @staticmethod
    def icon_content(id: int) -> Optional[SvgContent]:
        """
        Returns the content of the icon_svg (useful for creating a file)
        """

        sep = None
        icon_content: SvgContent = None
        with SqlAlchemyScopedSession() as db_session:
            try:
                stmt = select(MgmtSep).where(MgmtSep.id == id)
                sep = db_session.execute(stmt).scalar_one_or_none()
                is_empty = is_str_none_or_empty(sep.icon_svg)
                icon_content = SepIconConfig.empty_content() if is_empty else sep.icon_svg
            except Exception as e:
                icon_content = SepIconConfig.error_content()
                sidekick.app_log.error(f"Error retrieving icon content of SEP {id}: [{e}].")

        return icon_content

    @staticmethod
    def set_sep(sep: "MgmtSep") -> bool:
        """
        Saves a Sep record
        """
        from ..common.app_context_vars import sidekick

        done = False
        with SqlAlchemyScopedSession() as db_session:
            try:
                db_session.add(sep)
                db_session.commit()
                done = True
            except Exception as e:
                db_session.rollback()
                msg_error = f"Cannot update {MgmtSep.__tablename__}.id = {sep} | Error {e}."
                sidekick.app_log.error(msg_error)

        return done


# --- Table ---
class ReceivedFiles(Base):
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
    def get_user_records(
        id: int, user_id: int, email_sent: bool = True, had_reception_error: bool = False
    ) -> DBRecords:
        received_files = None
        msg_error = ""
        with SqlAlchemyScopedSession() as db_session:
            try:
                """----------------------------------------------
                /!\ Attention
                -------------------------------------------------
                    There is an index on the underlying table
                    (email_sent, had_reception_error, user_id, registered_at)
                    so if you are going change the where clause, be sure
                    to include these fields.
                """
                if id is not None:
                    stmt = select(ReceivedFiles).where(ReceivedFiles.id == id)
                else:
                    stmt = select(ReceivedFiles).where(
                        and_(
                            ReceivedFiles.email_sent == email_sent,
                            ReceivedFiles.had_reception_error == had_reception_error,
                        )
                    )
                    if user_id is not None:
                        stmt = stmt.where(ReceivedFiles.user_id == user_id)

                rows = db_session.scalars(stmt).all()
                received_files = DBRecords(ReceivedFiles.__tablename__, rows)
            except Exception as e:
                msg_error = (
                    f"Cannot load records from {ReceivedFiles.__tablename__}.where = {stmt} | Error {e}."
                )
                sidekick.app_log.error(msg_error)

        return received_files


# eof
