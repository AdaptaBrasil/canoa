"""
dv_version_helper.py
Reads the version of the installed `data_validate` (the pip package `canoa-data-validate`)
in a background thread, so the app start-up does not wait for it.

Why run the package instead of `pip show`: the version `pip show` gives lacks the sub-version (eg the `b732` of
0.7.65b732). The validator reports its own complete version, the one stored in user_data_files.validator_version,
so that is the one to compare with.
The package has no real `--version` option (argparse rejects it, exit code 2), but it prints a banner
"The ... version <version> initialized." on start-up, before parsing the arguments. That banner is parsed.

Called by igniter.py (start-up); later, reading `DVInfo.version` starts it again when the last attempt is older
than APP_REFRESH_DV_INFO_MIN. The result is kept in a `DVInfo` (see below), the one at `carranca.global_dv_info`:
`.version`, `.retrieved`, `.ready`. Like `global_ui_texts_cache`, it is created once and updated in place.
Same logic as carranca/tools/get_dv_version.py (a standalone copy: it can not import the app).

Equipe da Canoa -- 2026 + Anthropic Claude
mgd 2026-11-09
"""

# cSpell:ignore canoa

import re
import subprocess
import threading
from datetime import datetime, timedelta
from os import path
from typing import TYPE_CHECKING, Callable

from .py_helper import OS_IS_WINDOWS, decode_std_text

if TYPE_CHECKING:
    from ..common.Sidekick import Sidekick

DV_COMMAND = "canoa-data-validate"  # console script of the pip package, see run_validate.sh
FLAG_VERSION = "--version"
VERSION_PATTERN = re.compile(r"\bversion\s+(\S+)\s+initialized", re.IGNORECASE)  # "...version 0.7.65b732 initialized."
TIMEOUT_SECONDS = 60


class DVInfo:
    """
    data_validate's version, as read by `start_dv_version_lookup`.
    Until it is read: "?", None, False (`ready` is True only when the version was read).
    Created once (carranca.global_dv_info) and updated in place by the lookup thread,
    so `retrieved` tells a reader how old the version is.
    The three values live in one tuple that `set` replaces as a whole, so a reader never sees a half-set value.

    Reading again: `reading` is True while a lookup runs (only one at a time, see `begin_reading`);
    `is_stale` tells if the last attempt, successful or not, is older than the configured minutes
    (APP_REFRESH_DV_INFO_MIN).
    ⚠️ Reading `.version` refreshes it: when stale, it starts a lookup in the background (see `bind_refresh`)
    and still returns, at once, the current value; the next read gets the new one.
    """

    def __init__(self):
        self._state: tuple[str, datetime | None, bool] = ("?", None, False)
        self._reading = False
        self._attempted: datetime | None = None  # end of the last lookup, successful or not
        self._lock = threading.Lock()
        self._refresh: Callable[[], None] | None = None  # starts a lookup, see bind_refresh
        self._refresh_min = 0

    def bind_refresh(self, refresh: Callable[[], None], max_minutes: int) -> None:
        """`refresh` starts a lookup thread; `.version` calls it when the last attempt is older than `max_minutes`."""
        self._refresh = refresh
        self._refresh_min = max_minutes

    def _refresh_if_stale(self) -> None:
        if self._refresh and self.is_stale(self._refresh_min) and self.begin_reading():
            try:
                self._refresh()  # the thread it starts calls end_reading() when done
            except Exception:
                self.end_reading()  # no thread, or it would stay "reading" forever
                raise

    @property
    def reading(self) -> bool:
        return self._reading

    def begin_reading(self) -> bool:
        """True if the caller may start a lookup, False if one is already running."""
        with self._lock:
            if self._reading:
                return False
            self._reading = True
            return True

    def end_reading(self) -> None:
        with self._lock:
            self._attempted = datetime.now()
            self._reading = False

    def is_stale(self, max_minutes: int) -> bool:
        """True if a new lookup is due: none running, and the last attempt is older than `max_minutes` (0 = never)."""
        if max_minutes <= 0 or self._reading:
            return False
        if (attempted := self._attempted) is None:
            return True
        return datetime.now() - attempted >= timedelta(minutes=max_minutes)

    @property
    def version(self) -> str:
        self._refresh_if_stale()
        return self._state[0]

    @property
    def retrieved(self) -> datetime | None:
        return self._state[1]

    @property
    def ready(self) -> bool:
        return self._state[2]

    def set(self, version: str | None) -> None:
        """Called by the lookup thread with the version read; an empty one changes nothing."""
        if version:
            self._state = (version, datetime.now(), True)


def _find_command(data_validate_path: str) -> str:
    """The console script in the venv of the data_validate folder, "" if there is none."""
    if OS_IS_WINDOWS:
        # .cmd: a fake canoa-data-validate for tests on Windows
        candidates = [path.join(data_validate_path, ".venv", "Scripts", DV_COMMAND + ext) for ext in (".exe", ".cmd")]
    else:
        candidates = [path.join(data_validate_path, ".venv", "bin", DV_COMMAND)]

    return next((c for c in candidates if path.isfile(c)), "")


def read_dv_version(data_validate_path: str) -> tuple[str, str]:
    """Returns (version, "") or ("", the reason it was not read). Blocks until the command ends."""
    if not (command := _find_command(data_validate_path)):
        return "", f"{DV_COMMAND} was not found in the venv of [{data_validate_path}]"

    try:
        # exit code is ignored: `--version` is rejected by argparse (exit 2), after the banner was printed
        result = subprocess.run(
            [command, FLAG_VERSION],
            cwd=data_validate_path,  # as run_validate.sh does (cd)
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "", f"{DV_COMMAND} did not answer in {TIMEOUT_SECONDS} s"
    except OSError as e:
        return "", f"{command} could not run: {e}"

    if match := VERSION_PATTERN.search(decode_std_text(result.stdout)):
        return match.group(1), ""

    return "", f"no 'version <x> initialized' line in the output of {command} (exit code {result.returncode})"


def dv_app_and_path(config) -> tuple:
    """data_validate's app (ValidateProcessConfig.dv_app) and the path of its folder."""
    from ..config.ValidateProcessConfig import ValidateProcessConfig
    from .file_helper import path_remove_last_folder

    dv_app = ValidateProcessConfig().dv_app
    return dv_app, path.join(path_remove_last_folder(config.COMMON_PATH), dv_app.folder)


def _start_thread(sidekick: "Sidekick", dv_info: DVInfo, data_validate_path: str, ui_name: str) -> threading.Thread:
    # the caller has already done dv_info.begin_reading()
    def _lookup():
        try:
            try:
                version, error = read_dv_version(data_validate_path)
            except Exception as e:  # a thread's exception would only be printed by Python
                version, error = "", str(e)

            if version:
                dv_info.set(version)  # adds "retrieved" and "ready"
                sidekick.display.info(f"The {ui_name} version was read: {version}.")  # also goes to the log file
            else:
                sidekick.display.warn(f"The {ui_name} version could not be read: {error}.")
        finally:
            dv_info.end_reading()

    thread = threading.Thread(target=_lookup, name="dv_version", daemon=True)
    thread.start()
    return thread


def start_dv_version_lookup(
    sidekick: "Sidekick", dv_info: DVInfo, data_validate_path: str, ui_name: str
) -> threading.Thread:
    """
    Start-up lookup (igniter.py): marks `dv_info` as reading, and when done updates it and displays the result.
    It also tells `dv_info` how to read again (every APP_REFRESH_DV_INFO_MIN minutes, when `.version` is read).
    """
    dv_info.bind_refresh(
        lambda: _start_thread(sidekick, dv_info, data_validate_path, ui_name), int(sidekick.config.APP_REFRESH_DV_INFO_MIN)
    )
    dv_info.begin_reading()
    return _start_thread(sidekick, dv_info, data_validate_path, ui_name)


# eof
