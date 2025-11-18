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
from logging import Logger
from datetime import datetime

from .Display import Display
from ..config.BaseConfig import BaseConfig


class Sidekick:
    """
    A handy hub for sidekick objects for flask + Python (ƒ+py)
    """

    def __init__(self, config: BaseConfig, display: Display):
        from ..config.DynamicConfig import DynamicConfig  # Avoid Circular 2025.12.03

        self.config: DynamicConfig = config
        self.app_name = self.config.APP_NAME
        self.debugging = self.config.APP_DEBUGGING
        self.display = display
        self.started_at = datetime.now()
        self.log_filename = ''
        display.debug(f"{self.__class__.__name__} was created.")

    # TODO remove almost unused
    @property
    def app(self) -> Flask:
        return current_app

    @property
    def app_log(self) -> Logger:
        return self.app.logger

    def __str__(self):
        return f"{self.__class__.__name__} the ƒ+py dev's companion"


# eof
