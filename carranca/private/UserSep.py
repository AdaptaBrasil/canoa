"""
Class for handling logged user SEPs information.

See AppUser.seps: List[UserSEP]

Equipe da Canoa -- 2025
mgd
"""

# spell:ignore Mgmt

from typing import TYPE_CHECKING, List, Dict, Any

from .IdToCode import IdToCode
from ..helpers.types_helper import ErrorMessage


if TYPE_CHECKING:
    type UserSepList = List["UserSep"]
    type UserSepDict = Dict[str, Any]
    type UserSepsRtn = UserSepList | ErrorMessage


class UserSep:
    """
    Contains UI-related information for each SEP.
    This class is resource-intensive to instantiate
    due to the 'icon_url' attribute, which ensures
    that an icon file is available at the specified URL.
    If the icon file is missing, it will be created.

    see .models.MgmtUserSeps
    """

    # obfuscate the id when is public
    id_to_code = IdToCode()

    @staticmethod
    def to_id(code: str) -> int:
        return UserSep.id_to_code.decode(code)

    @property
    def code(self) -> str:
        return UserSep.id_to_code.encode(self.id)

    def __init__(
        self,
        id: int,
        name: str,
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
        self.scm_name = scm_name
        self.fullname = fullname
        self.description = description
        self.visible = visible
        self.icon_file_name = SepIconMaker.get_file_name(icon_file_name)
        self.icon_url = icon_url

    id: int
    name: str
    scm_name: str
    fullname: str
    description: str
    visible: bool
    icon_file_name: str
    icon_url: str  # expensive to 'calculate', so it is optional


# eof
