"""
Public Tables
Part of Public Access Control Processes

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore nullable sqlalchemy joinedload, SQLA

from carranca import global_sqlalchemy_scoped_session, global_login_manager

from typing import Optional, Any, List
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
from sqlalchemy.orm import relationship, joinedload
from flask_login import UserMixin

from ..helpers.db_records.DBRecords import DBRecords

from ..models import SQLABaseTable
from ..helpers.pw_helper import hash_pass
from ..helpers.py_helper import is_str_none_or_empty
from ..helpers.db_helper import db_fetch_rows
from ..private.RolesAbbr import RolesAbbr
from ..common.app_constants import APP_LANG


# --- Table ---
class User(SQLABaseTable, UserMixin):

    __tablename__ = "users"

    # https://docs.sqlalchemy.org/en/13/core/type_basics.html
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_role = Column(Integer, ForeignKey("roles.id"))
    lang = Column(String(8), default=APP_LANG)
    username = Column(String(100), unique=True)
    username_lower = Column(String(100), Computed(""))
    email = Column(String(64), unique=True)
    disabled = Column(Boolean, default=False)

    password = Column(LargeBinary)
    # OBSOLETE
    # mgmt_sep_id = Column(Integer, unique=True)
    last_login_at = Column(DateTime, nullable=True)
    recover_email_token = Column(String(100), nullable=True, unique=True)
    recover_email_token_at = Column(DateTime, Computed(""))
    password_failures = Column(Integer, default=0)
    password_failed_at = Column(DateTime)

    email_confirmed = Column(Boolean, Computed("email_confirmed", persisted=True))

    role = relationship("Role", back_populates="users")
    debug = Column(Boolean, default=False)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (tra_vis flake8 test)
                value = value[0]

            if property == "password":
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

    def get_where(**filter: Any) -> "User":
        """
        Select a user by a unique filter
        """

        def _get_data(db_session: Session) -> "User":
            user = db_session.query(User).options(joinedload(User.role)).filter_by(**filter).first()
            return user

        _, _, user = db_fetch_rows(_get_data, User.__tablename__)
        return user

    @staticmethod
    def get_all_users(
        arg_where: ColumnExpressionArgument[bool], arg_order: Optional[Column] = None
    ) -> List["User"]:  # DBRecords:
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
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    abbr = Column(String(3))  # see user_roles.py
    users = relationship("User", back_populates="role")


def get_user_role_abbr(user_id: int, user_role_id: int) -> RolesAbbr:
    """
    Retrieves and checks a user role against enum
    """

    abbr = None
    if not user_role_id is None:
        with global_sqlalchemy_scoped_session() as db_session:
            try:
                row = db_session.query(Role).filter_by(id=user_role_id).first()
                abbr = None if row is None else row.abbr
            except Exception as e:
                from ..common.app_context_vars import sidekick

                sidekick.app_log.error(
                    f"Error retrieving user {user_id} role {user_role_id}: [{e}]."
                )

    return abbr


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
            sidekick.app_log.error(f"Error retrieving user {filter}: [{e}].")

    return user


def persist_user(record: any, task_code: int = 1) -> None:
    """
    Updates a user's record
    """
    from ..common.app_context_vars import sidekick

    with global_sqlalchemy_scoped_session() as db_session:
        task_code = 0
        try:
            task_code += 1
            if db_session.object_session(record) is not None:
                sidekick.app_log.debug("User record needs an expunge.")
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
def user_loader(id):
    # current_user #
    user = User.get_where(id=id)
    return user


# TODO, seems that this make a user name before log process has finished
@global_login_manager.request_loader
def request_loader(request):
    username = "" if len(request.form) == 0 else request.form.get("username", "")
    user = (
        None if is_str_none_or_empty(username) else User.get_where(username_lower=username.lower())
    )
    return user


# eof
