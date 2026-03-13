"""
Class for handling the 'jinja user' (seen in *.j2 files) information.

This class shrinks the amount of information that is passed to the Jinja2 templates.

Equipe da Canoa -- 2025
mgd
"""

# cSpell:ignore

from .AppUser import AppUser
from ..common.app_constants import APP_LANG


class JinjaUser:
    """
    A user object for use in Jinja2 templates, containing only
    the essential information to ensure security.
    """

    def __init__(self, app_user: AppUser):
        from ..common.app_context_vars import sidekick

        self.ready = app_user.ready if app_user else False

        if self.ready:
            sidekick.display.debug(f"{self.__class__.__name__} was created.")
            self.lang = app_user.lang
            self.name = app_user.name
            self.role = app_user.role_name
            self.debug = app_user.is_support or app_user.debug
            self.power = app_user.is_power
            self.email_verified = app_user.email_verified
        else:
            sidekick.display.debug(f"{self.__class__.__name__} was reset.")
            self.lang = APP_LANG  # locale.getdefaultlocale()[0]  # TODO, check if available
            self.name = "?"
            self.role = ""
            self.debug = False
            self.power = False
            self.email_verified = False

    def __repr__(self):
        user_info = "Unknown" if not self.ready else f"{self.name} [{self.lang}]"
        return f"<{self.__class__.__name__}({user_info})>"


# eof
