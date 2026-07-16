"""
 MgmtEmailSep Table

Equipe da Canoa -- 2024

"""

# cSpell:ignore: nullable sqlalchemy

from datetime import datetime
from sqlalchemy import Computed, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from ..base import CanoaBaseTable


class MgmtEmailSep(CanoaBaseTable):
    """
    This *Updatable view `vw_mgmt_email_sep` exposes
    columns to assist in sending emails to users when
    the SEP assigned to them is changed by an admin.
        ./private/sep_mgmt/send_email.py
        updates email_at and email_error
    """

    __tablename__ = "vw_mgmt_email_sep"
    __code_seed__ = 2

    # id: in CanoaBase

    new_user_name: Mapped[str] = mapped_column(String, Computed(""))  # read only columns
    new_user_email: Mapped[str] = mapped_column(String, Computed(""))
    old_user_name: Mapped[str] = mapped_column(String, Computed(""))
    old_user_email: Mapped[str] = mapped_column(String, Computed(""))
    sep_fullname: Mapped[str] = mapped_column(String, Computed(""))
    batch_code: Mapped[str] = mapped_column(String(10))
    email_at: Mapped[datetime | None] = mapped_column(DateTime)
    email_error: Mapped[str | None] = mapped_column(String(400))


# eof
