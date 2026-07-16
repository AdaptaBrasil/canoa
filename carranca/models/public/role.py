"""
 Role Table

Equipe da Canoa -- 2024

"""

# cSpell:ignore sqlalchemy

from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import CanoaBaseTable

if TYPE_CHECKING:
    from .user import User  # avoid circular import at runtime; user.py imports Role at module level


class Role(CanoaBaseTable):
    """
    User's role in Canoa
    There is no UI for this table,
    use your DB Manager

    ⚠️ KEEP sync with private.RolesAbr
    """

    __tablename__ = "roles"
    __code_seed__ = 13

    # id: in CanoaBase
    # description: String(64)
    name: Mapped[str] = mapped_column(String(64))
    abbr: Mapped[str] = mapped_column(String(3))  # see user_roles.py
    users: Mapped["User"] = relationship("User", back_populates="role")


# eof
