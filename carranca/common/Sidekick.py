"""
Sidekick
  Sidekick is class to keep easily accessible
  frequently used objects

  This object is initialized in package/__init__.py

      Sidekick objects:
      ├── config         config.Config + app.config (see sidekick.py header for more info)
      ├── app_log        Flask's app logger
      └── display        mgd's simple text display to console


  app.config vs config
  ------------------------
  `app.config` has almost all the attributes of the `config``
  *plus* those of Flask.

  So to keep it 'mode secure' and avoid 'circular imports',
  use sidekick.config

  app_log == app.Logger
  ---------------------

  v1 Shared mgd 2024-07-22,10-07
  v2 Sidekick 2024.10.23
  v3 Lifetime changed
     request and module scoped variables:
          module:   _module_sidekick
          request:  g._sidekick
          session: (not used here)
          sk = session.get('sidekick', None)
          session['sidekick'] = _recreate_sidekick()
          see:
          app_context_vars.py

"""

# cSpell:ignore sqlalchemy mgd appcontext

from flask import Flask, current_app
from typing import TYPE_CHECKING
from logging import Logger
from datetime import datetime
from flask_login import current_user
from .Display import Display
from ..common.app_constants import APP_NAME

if TYPE_CHECKING:
    from ..models.public import User
    from ..config.DynamicConfig import DynamicConfig  # Avoid Circular 2024.11.03


class Sidekick:
    """
    A handy hub for sidekick objects for flask + Python (ƒ+py)
    """

    def __init__(self, config: "DynamicConfig", display: Display):

        # from ..models.public import User # Avoid early access

        self.config: DynamicConfig = config
        self.app_name = APP_NAME
        self.debugging = True if self.config.APP_DEBUGGING else False
        self.log_text = self.config.SIDEKICK_LOG
        self.display = display
        self.started_at = datetime.now()
        self.log_filename = ""
        echo = ""
        if self.config.SIDEKICK_LOG:
            display.echo = self._echo
            echo = " and is echoing to the log file."
        display.debug(f"{self.__class__.__name__} was created{echo}.")

    def now(self) -> datetime:
        return datetime.now()

    # TODO remove almost unused
    @property
    def app(self) -> Flask:
        return current_app

    @property
    def user(self) -> "User":
        _user: "User" = current_user
        return _user

    @property
    def app_log(self) -> Logger:
        return self.app.logger

    def occurrences(self, kind: Display.Kind) -> int:
        _count = self.display.occurrences(kind)
        return _count

    def occurrences_map(self, filter: int = -1) -> dict[Display.Kind, int]:
        _count = self.display.occurrences
        return {kind: _count(kind) for kind in Display.Kind if _count(kind) > filter}

    def _echo(self, kind: Display.Kind, log_text: str):
        if not (self.app and self.app.logger):
            # Todo create a buffer
            return

        try:
            user_id = f"{(current_user.id if current_user.is_active else 0):03d}"
        except Exception as e:
            user_id = "usr!"

        text = f"{user_id}|{log_text}"

        match kind:
            case Display.Kind.INFO:
                self.app_log.info(text)
            case Display.Kind.WARN:
                self.app_log.warning(text)
            case Display.Kind.ERROR:
                self.app_log.error(text)
            case Display.Kind.DEBUG:
                self.app_log.debug(text)

    def __str__(self):
        return f"{self.__class__.__name__} the ƒ+py dev's companion"


# eof
