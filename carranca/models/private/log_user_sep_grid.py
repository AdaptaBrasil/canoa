"""
 Private Models
    vw_log_user_sep
    read-only audit-log grid for log_user_sep (SEP creation/removal/manager-assignment history)

Equipe da Canoa -- 2026.07.15
"""

# cSpell:ignore: nullable sqlalchemy duovigesimal

from datetime import datetime
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import CanoaBaseView

# operation: single-char code from log_user_sep, decoded here (not in SQL) per team decision 2026-07-15
OPERATION_LABELS = {
    "S": "Set",
    "R": "Removed",
    "I": "Inserted",
    "E": "Edited",
    "D": "Deleted",
    "C": "Schema changed",
}


class LogUserSepGrid(CanoaBaseView):
    __tablename__ = "vw_log_user_sep"
    __code_seed__ = 14

    id_sep: Mapped[int] = mapped_column(Integer)
    sep_fullname: Mapped[str | None] = mapped_column(String)
    id_users: Mapped[int | None] = mapped_column(Integer)
    user_name: Mapped[str | None] = mapped_column(String)
    id_users_prior: Mapped[int | None] = mapped_column(Integer)
    user_prior_name: Mapped[str | None] = mapped_column(String)
    done_at: Mapped[datetime] = mapped_column(DateTime)
    done_by: Mapped[int] = mapped_column(Integer)
    done_by_name: Mapped[str | None] = mapped_column(String)
    batch_code: Mapped[str] = mapped_column(String(10))
    operation: Mapped[str | None] = mapped_column(String(1))
    email_at: Mapped[datetime | None] = mapped_column(DateTime)
    email_error: Mapped[str | None] = mapped_column(String(800))

    @staticmethod
    def operation_label(operation: str | None) -> str:
        return OPERATION_LABELS.get(operation or "", "?")


# eof
