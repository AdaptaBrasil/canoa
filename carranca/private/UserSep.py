"""
Class for handling logged user SEPs information.

See AppUser.seps: List[UserSEP]

Equipe da Canoa -- 2025
mgd
"""

# spell:ignore Mgmt

from typing import TYPE_CHECKING, List

from ..helpers.types_helper import Error_Message
from ..models.private.mgmt_seps_user import MgmtSepsUser

if TYPE_CHECKING:
    type UserSepList = List["UserSep"]
    type UserSepsRtn = UserSepList | Error_Message


class UserSep:
    """
    Contains UI-related information for each SEP.
    This class is resource-intensive to instantiate
    due to the 'icon_url' attribute, which ensures
    that an icon file is available at the specified URL.
    If the icon file is missing, it will be created.

    see .models.MgmtUserSeps
    """

    @staticmethod
    def to_id(code: str) -> int:
        return MgmtSepsUser.to_id(code)

    @property
    def code(self) -> str:
        return MgmtSepsUser.to_code(self.id)

    def __init__(
        self,
        id: int,
        name: str,
        spd_id: int,
        spd_name: str,
        scm_name: str,
        fullname: str,
        description: str,
        visible: bool,
        icon_file_name: str,
        icon_url: str = "",
    ):
        from .SepIconMaker import SepIconMaker

        self.id = id
        self.name = name
        self.spd_id = spd_id
        self.spd_name = spd_name
        self.scm_name = scm_name
        self.fullname = fullname
        self.description = description
        self.visible = visible
        self.icon_file_name = SepIconMaker.get_file_name(icon_file_name)
        self.icon_url = icon_url

    id: int
    name: str
    spd_id: int
    spd_name: str
    scm_name: str
    fullname: str
    description: str
    visible: bool
    icon_file_name: str
    icon_url: str  # expensive to 'calculate', so it is optional


# eof
