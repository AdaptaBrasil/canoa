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

# cSpell:ignore sqlalchemy mgd appcontext timespec

from flask import Flask, current_app, has_request_context
from typing import TYPE_CHECKING, cast
from collections import deque
from logging import Logger
from datetime import date, datetime
from .Display import Display
from flask_login import current_user
from ..common.app_constants import APP_NAME

if TYPE_CHECKING:
    from ..models.public.user import User
    from ..config.DynamicConfig import DynamicConfig  # Avoid Circular 2024.11.03


class Sidekick:
    """
    A handy hub for sidekick objects for flask + Python (ƒ+py)
    """

    _echoing = False

    def __init__(self, config: "DynamicConfig", display: Display):

        # from ..models.public.user import User # Avoid early access

        self.config: DynamicConfig = config
        self.app_name = APP_NAME
        self.debugging = True if self.config.APP_DEBUGGING else False
        self.log_text = self.config.SIDEKICK_LOG
        self.display = display
        self.started_at = datetime.now()
        self.log_filename = ""
        # Display lines echoed before the log file exists (the igniter's), kept for attach_logger()
        self._echo_buffer: deque[tuple[Display.Kind, str]] = deque(maxlen=500)
        self._echo_logger: Logger | None = None
        echo = ""
        pending = display.take_pending_echo()  # the igniter's lines, printed before this Sidekick existed
        if self.config.SIDEKICK_LOG:
            display.echo = self._echo
            for kind, text in pending:
                self._echo(kind, text)  # no log file yet: they wait in _echo_buffer, for attach_logger()
            echo = " and is echoing to the log file."
        display.debug(f"{self.__class__.__name__} was created{echo}.")

    def now(self) -> datetime:
        return datetime.now()

    @staticmethod
    def to_iso_dt(value: date | datetime | None) -> str | None:
        """
        ISO date-time without a time zone (eg "2026-11-06T13:26:28.558"), so JS `new Date()` reads it as local time.
        Use it for dates sent to JS with `tojson`: Flask labels naive datetimes as GMT, and JS shifts them (eg -3h).
        The DB's naive datetimes are local time; a `date` gets the local midnight (JS reads a date-only ISO as UTC).
        Milliseconds: the ECMAScript date-time format has 3 fraction digits, Python's default is 6.
        `None` stays `None`.
        """
        if value is None:
            return None
        dt = value if isinstance(value, datetime) else datetime.combine(value, datetime.min.time())
        return dt.isoformat(timespec="milliseconds")

    # TODO remove almost unused
    @property
    def app(self) -> Flask:
        return current_app

    @property
    def user(self) -> "User":
        _user: "User" = cast("User", current_user)
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

    def attach_logger(self, logger: Logger):
        """
        Called by create_app() when the log file's handler exists (no app context yet at that time):
        from now on the Display lines are echoed to `logger`, and the lines kept so far go first.
        """
        self._echo_logger = logger
        buffered = list(self._echo_buffer)
        self._echo_buffer.clear()
        for kind, log_text in buffered:
            self._echo(kind, log_text)

    def _echo(self, kind: Display.Kind, log_text: str):
        # attach_logger()'s logger (start-up) or else the current app's
        logger = self._echo_logger or (self.app.logger if self.app else None)
        if logger is None:
            # no log file yet (the igniter's lines): kept for attach_logger()
            self._echo_buffer.append((kind, log_text))
            return

        if self._echoing:
            # avoid a  recursive error
            return

        self._echoing = True
        user_id = "sys"  # no request: start-up
        try:
            if has_request_context():
                user_id = f"{(current_user.id if current_user.is_active else 0):03d}"
        except Exception as e:
            logger.debug(f"Current user load error in {self.__class__.__name__}: [{e}]")
            user_id = "usr!"
        finally:
            self._echoing = False

        text = f"{user_id}|{log_text}"

        match kind:
            case Display.Kind.PROMPT | Display.Kind.ELAPSED | Display.Kind.USER:
                pass  # not logged, console only
            case Display.Kind.INFO:
                logger.info(text)
            case Display.Kind.WARN:
                logger.warning(text)
            case Display.Kind.ERROR:
                logger.error(text)
            case Display.Kind.DEBUG:
                logger.debug(text)
            case Display.Kind.FATAL:
                logger.critical(text)
            case _:
                logger.critical(f"Unknown kind '{kind}', with text:")
                logger.info(text)

    def __str__(self):
        return f"{self.__class__.__name__} the ƒ+py dev's companion"


# eof
