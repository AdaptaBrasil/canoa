"""
Class for handling logged user information.

This module extends Flask's `current_user` with additional utilities specific to Canoa.

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore MgmtSep mgmt

from flask_login import current_user
from typing import TYPE_CHECKING

from .RolesAbbr import RolesAbbr

from ..common.app_constants import APP_LANG
from ..common.app_error_assistant import AppStumbled
from ..helpers.user_helper import get_user_code, get_user_folder
from ..helpers.types_helper import ErrorMessage

if TYPE_CHECKING:
    from .UserSep import UserSepList

# App needed information of the logged user.
class AppUser:
    def __init__(self):
        from ..common.app_context_vars import sidekick
        from .SepIconMaker import SepIconMaker  # Avoid Circular 2025.02.20

        self.ready = current_user.is_authenticated if current_user else False

        if not self.ready:
            sidekick.display.debug(f"{self.__class__.__name__} was reset.")
            self.lang = APP_LANG  # TODO: None -> use Browser default
            self.name = "?"
            self.debug = False
            self.id = -1
            self.disabled = True
            self.email = ""
            self.code = "0"
            self.folder = ""
            self.path = ""
            self.role_abbr = RolesAbbr.Void.value
            self.role_name = ""
            self.is_adm = False
            self.is_support = False
            self.is_power = False
        else:
            sidekick.display.debug(f"{self.__class__.__name__} was created.")
            self.lang = current_user.lang
            self.name = current_user.username
            self.debug = current_user.debug
            self.id = current_user.id
            self.disabled = current_user.disabled
            self.email = current_user.email
            self.code = get_user_code(current_user.id)
            self.folder = get_user_folder(current_user.id)
            self.path = SepIconMaker.local_path
            self.role_abbr: str = current_user.role.abbr
            self.role_name: str = current_user.role.name
            self.is_adm: bool = self.role_abbr == RolesAbbr.Admin.value
            self.is_support: bool = self.role_abbr == RolesAbbr.Support.value
            self.is_power: bool = (
                self.is_adm
                # or (self.is_support and sidekick.debugging)
                or self.name in ["Mauro", "Miguel"]
            )

    @property
    def seps(self) -> "UserSepList":
        from ..common.app_context_vars import user_seps

        result: "UserSepList" = []
        if not self.ready:
            result = []
        elif isinstance(us_list := user_seps, list):
            result: "UserSepList" = us_list
        else:
            msg: ErrorMessage = str(us_list) if isinstance(user_seps, str) else "Error loading user SEP."
            raise AppStumbled(msg)

        return result

    def __repr__(self):
        user_info = "Unknown" if not self.ready else f"{self.name} [id:{self.id}]"
        return f"<{self.__class__.__name__}({user_info})>"


# eof
