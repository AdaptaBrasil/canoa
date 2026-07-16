"""
 UserDataFiles Table

Equipe da Canoa -- 2024

"""

# cSpell:ignore: nullable sqlalchemy sessionmaker

from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Mapped, mapped_column, Session
from ... import global_sqlalchemy_scoped_session
from ..base import CanoaBaseTable
from ...common.app_context_vars import sidekick


class UserDataFiles(CanoaBaseTable):
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
    __code_seed__ = 6

    # register, pk/fk/uniqueKey
    # id: in CanoaBase
    ticket: Mapped[str | None] = mapped_column(String(40), unique=True)
    id_sep: Mapped[int | None] = mapped_column(Integer)  # fk
    id_spd: Mapped[int | None] = mapped_column(Integer)  # fk  spatial_data_files
    id_users: Mapped[int | None] = mapped_column(Integer)  # fk
    log_file_name: Mapped[str | None] = mapped_column(String(200))  # use in case of error
    # register, file info
    file_name: Mapped[str | None] = mapped_column(String(140))
    file_size: Mapped[int | None] = mapped_column(Integer)
    file_crc32: Mapped[int | None] = mapped_column(BigInteger)  # crc32 can exceed int4 range
    user_receipt: Mapped[str | None] = mapped_column(String(15))

    # register, sys info
    db_version: Mapped[str | None] = mapped_column(String(12))
    app_version: Mapped[str | None] = mapped_column(String(12))
    process_version: Mapped[str | None] = mapped_column(String(12))

    from_os: Mapped[str | None] = mapped_column(String(1))
    file_origin: Mapped[str | None] = mapped_column(String(1))
    original_name: Mapped[str | None] = mapped_column(String(80), nullable=True, default=None)

    ## register
    a_received_at: Mapped[datetime | None] = mapped_column(DateTime)
    b_process_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    c_check_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    d_register_started_at: Mapped[datetime | None] = mapped_column(DateTime)

    ## submit & email & process
    e_unzip_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    f_submit_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    g_report_ready_at: Mapped[datetime | None] = mapped_column(DateTime)

    ## submit
    validator_version: Mapped[str | None] = mapped_column(String(16))
    validator_result: Mapped[str | None] = mapped_column(String(1024))
    report_errors: Mapped[int | None] = mapped_column(Integer)
    report_warns: Mapped[int | None] = mapped_column(Integer)
    report_tests: Mapped[int | None] = mapped_column(Integer)

    ## submit & email
    h_email_started_at: Mapped[datetime | None] = mapped_column(DateTime)

    ## email.py
    email_sent: Mapped[bool | None] = mapped_column(Boolean, default=False)

    ## process, on exit
    # error_handled, exit_code: DB-trigger/legacy managed columns, not mapped here
    error_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    success_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    z_process_end_at: Mapped[datetime | None] = mapped_column(DateTime)

    ## Set on trigger
    # registered_at, at insert
    # db_version
    # email_sent_at, when email_sent = T
    # error_at, when error_code not 0
    # Special
    # error_handled, when admin handles the error (TODO)

    ## obsolete  2026.04.02
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
                sidekick.display.error(msg_error)
                raise DatabaseError(msg_error, None, e)
        return None

    # Public insert/update
    @staticmethod
    def insert(uTicket: str, **kwargs) -> None:
        UserDataFiles._ins_or_upd(True, uTicket, **kwargs)
        return None

    @staticmethod
    def update(uTicket: str, **kwargs) -> None:
        UserDataFiles._ins_or_upd(False, uTicket, **kwargs)
        return None


# eof
