"""
Public Tables
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore nullable sqlalchemy joinedload, SQLA

from carranca import global_sqlalchemy_scoped_session, global_login_manager

from flask import Request
from typing import Optional, Any, List
from datetime import datetime
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import ColumnExpressionArgument
from sqlalchemy import (
    String,
    select,
    Column,
    Integer,
    Boolean,
    DateTime,
    Computed,
    ForeignKey,
    LargeBinary,
)
from sqlalchemy.orm import relationship, joinedload, Mapped, mapped_column
from flask_login import UserMixin

from ..helpers.db_records.DBRecords import DBRecords

from ..models import SQLABaseTable
from ..helpers.pw_helper import hash_password
from ..helpers.py_helper import is_str_none_or_empty, to_str
from ..helpers.db_helper import db_fetch_rows
from ..private.RolesAbbr import RolesAbbr
from ..common.app_constants import APP_LANG


# --- Table ---
class User(SQLABaseTable, UserMixin):

    __tablename__ = "users"

    # https://docs.sqlalchemy.org/en/13/core/type_basics.html
    # 2026-02-20:
    # `mapped_column` is used to avoid the need of type annotations in the class properties,
    #     which are already defined by the Column() calls
    # see carranca\public\access_control\password_recovery.py
    # for example of how it simplifies the code and avoids mistakes in type annotations

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_role: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))
    lang: Mapped[str | None] = mapped_column(String(8), default=APP_LANG)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    username_lower: Mapped[str] = mapped_column(String(100), Computed(""))
    email: Mapped[str] = mapped_column(String(64), unique=True)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)

    password: Mapped[bytes] = mapped_column(LargeBinary)
    # OBSOLETE  2026.04.02
    # mgmt_sep_id = Column(Integer, unique=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # this columns names are confusing, they are for password recovery process, not for email confirmation
    # It should be renamed to "recover_pw_token" and "recover_pw_token_at"
    recover_email_token: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    recover_email_token_at: Mapped[datetime] = mapped_column(DateTime, Computed(""))
    # this columns names are confusing, they are for login failures
    password_failures: Mapped[int] = mapped_column(Integer, default=0)
    password_failed_at: Mapped[datetime] = mapped_column(DateTime)

    # 2026-01
    verify_email_token: Mapped[str | None] = mapped_column(String(8), nullable=True, unique=False)
    verify_email_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    email_verified: Mapped[bool] = mapped_column(Boolean, Computed("email_verified", persisted=True))
    # is is hidden column email_verified_at = Column(DateTime, nullable=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    debug: Mapped[bool] = mapped_column(Boolean, default=False)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (tra_vis flake8 test)
                value = value[0]

            if property == "password":
                value = hash_password(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

    @staticmethod
    def get_where_name_is(name: str) -> "User":
        return User.get_where(username_lower=to_str(name).lower())

    @staticmethod
    def get_where_email_is(email: str) -> "User":
        return User.get_where(email=to_str(email).lower())

    @staticmethod
    def get_where(**filter: Any) -> "User":
        """
        Select a user by a unique filter
        """

        def _get_data(db_session: Session):
            user = db_session.query(User).options(joinedload(User.role)).filter_by(**filter).first()
            return user

        _, _, user = db_fetch_rows(_get_data, User.__tablename__)
        return user

    @staticmethod
    def get_all_users(arg_where: ColumnExpressionArgument[bool], arg_order: Optional[Column] = None) -> List["User"]:  # DBRecords:
        """
        Fetches a list of all users (id, id_role, username, email, disabled)
        from the `users` table.
        """

        def _get_data(db_session: Session):
            stmt = (
                select(User.id, User.id_role, User.username, User.email, User.disabled)
                .where(arg_where)
                .order_by(User.username_lower if arg_order is None else arg_order)
            )

            usr_rows = db_session.execute(stmt).all()
            usr_list = DBRecords(stmt, usr_rows)
            return usr_list

        _, _, seps_recs = db_fetch_rows(_get_data, User.__tablename__)
        return seps_recs


# --- Table ---
class Role(SQLABaseTable):
    """
    User's role in Canoa
    """

    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    abbr: Mapped[str] = mapped_column(String(3))  # see user_roles.py
    users: Mapped["User"] = relationship("User", back_populates="role")


def get_user_where(**filter: Any) -> User:
    """
    Select a user by a unique filter
    """
    from ..common.app_context_vars import sidekick

    user = None
    db_session: Session
    with global_sqlalchemy_scoped_session() as db_session:
        try:
            # stmt = select(User).filter_by(**filter)
            # user =  db_session.execute(stmt).scalar_one_or_none()
            user = db_session.query(User).options(joinedload(User.role)).filter_by(**filter).first()
        except Exception as e:
            user = None
            sidekick.display.error(f"Error retrieving user {filter}: [{e}].")

    return user


def persist_user(record: User, task_code: int = 1) -> None:
    """
    Updates a user's record
    """
    from ..common.app_context_vars import sidekick

    with global_sqlalchemy_scoped_session() as db_session:
        task_code = 0
        try:
            task_code += 1
            if db_session.object_session(record) is not None:
                sidekick.display.debug("User record needs an expunge.")
                task_code += 2
                db_session.expunge(record)
            task_code = 3
            db_session.add(record)
            task_code += 1
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            e.task_code = task_code
            raise DatabaseError(e)


# -- Important for user flask manager ---------------------


@global_login_manager.user_loader
def user_loader(id: str) -> UserMixin | None:
    """
    Flask-Login user_loader callback.

    Parameters
    ----------
    user_id : str
        The user ID stored in the session (always passed as a string).
        (it can be e-mail or username or PK id, depending on your implementation)

    Returns
    -------
    UserMixin | None
        The user object corresponding to the given ID, or None if not found.
    """
    try:
        user_id = int(id)  # convert to int if your DB uses Integer PKs
    except ValueError:
        return None

    user = User.get_where(id=user_id)
    return user


# TODO, seems that this make a user name before log process has finished
@global_login_manager.request_loader
def request_loader(request: Request) -> UserMixin | None:
    username = "" if len(request.form) == 0 else request.form.get("username", "")
    user = None if is_str_none_or_empty(username) else User.get_where(username_lower=username.lower())
    return user


# eof
