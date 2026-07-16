"""
 User Table
Part of Public Access Control Processes

Equipe da Canoa -- 2024

"""

# cSpell:ignore nullable sqlalchemy joinedload

from flask import Request
from typing import Any, List, Optional
from datetime import datetime
from sqlalchemy import Boolean, Column, Computed, DateTime, ForeignKey, Integer, LargeBinary, String, func, select
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, Session, joinedload, mapped_column, relationship
from sqlalchemy.sql.expression import ColumnExpressionArgument

from ... import global_login_manager
from .role import Role
from ..base import CanoaBaseTable
from ...helpers.pw_helper import hash_password
from ...helpers.db_helper import db_fetch_rows
from ...helpers.py_helper import is_str_none_or_empty
from ...common.app_constants import APP_LANG
from ...helpers.db_records.DBRecords import DBRecords


class User(CanoaBaseTable, UserMixin):

    __tablename__ = "users"
    __code_seed__ = 12

    # https://docs.sqlalchemy.org/en/13/core/type_basics.html
    # 2026-02-20:
    # `mapped_column` is used to avoid the need of type annotations in the class properties,
    #     which are already defined by the Column() calls
    # see carranca\public\access_control\password_recovery.py
    # for example of how it simplifies the code and avoids mistakes in type annotations

    # id: in CanoaBase
    # registered_at, disabled_at, password_changed_at, email_changed_at: DB-trigger managed, not mapped here
    id_role: Mapped[int] = mapped_column(Integer, ForeignKey("canoa.roles.id"))
    lang: Mapped[str | None] = mapped_column(String(8), default=APP_LANG)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    username_lower: Mapped[str] = mapped_column(String(100), Computed(""))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)

    password: Mapped[bytes] = mapped_column(LargeBinary)
    # OBSOLETE  2026.04.02
    # mgmt_sep_id = Column(Integer, unique=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_logout_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
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
        return User.get_where(username_lower=func.lower(name))

    @staticmethod
    def get_where_email_is(email: str) -> "User":
        return User.get_where(email=func.lower(email))

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


# -- Important for flask's user manager ---------------------
# ---------------------------------------------------------
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
