"""
 LogUserSep Table

Equipe da Canoa -- 2024

"""

# cSpell:ignore: nullable sqlalchemy duovigesimal

from datetime import datetime
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from ..base import CanoaBaseTable


class LogUserSep(CanoaBaseTable):
    """
    Keeps track of SEP management user (actual and last one)
    and
    insert and editions to table Sep
    """

    __tablename__ = "log_user_sep"
    __code_seed__ = 1

    # id: in CanoaBase

    id_sep: Mapped[int] = mapped_column(Integer, nullable=False)
    # Set NULL when remove sep from user (=id_users_prior)
    id_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # The user ID of the previous owner of the SEP, or None if none was assigned
    id_users_prior: Mapped[int | None] = mapped_column(Integer, nullable=True)
    done_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    done_by: Mapped[int] = mapped_column(Integer, nullable=False)  # The admin user who performed the action (not the new owner: see id_users)
    # (days since 2024.11.01).(ms) both in base duovigesimal (22)
    batch_code: Mapped[str] = mapped_column(String(10), nullable=False)
    email_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_error: Mapped[str | None] = mapped_column(String(800), nullable=True)
    # (S)et, (Removed | (Edited, marked as (Deleted | (Change schema. For insert, see sep.ins_at.
    operation: Mapped[str | None] = mapped_column(String(1), nullable=True)


# eof
