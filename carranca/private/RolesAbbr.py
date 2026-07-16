"""
*User Roles*
This is a helper to facilitate
the selection of users by 'rol'
(users.id_role) via roles.role


Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore Setorista

from enum import Enum

"""
    carranca/private/models.py Table Role
    This are import to determine the User's role
        Is he/she the administrator?
        maybe support/coder?

"""


class RolesAbbr(Enum):
    Void = "VOD"  # not initialized/Deactivated
    Admin = "ADM"
    Setorista = "SEP"
    Support = "SPT"


# eof
