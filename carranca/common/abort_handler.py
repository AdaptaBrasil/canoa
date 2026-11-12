"""
abort_handler

    Shared except-block for the file-download routes (sep_ids_download.py,
    spd_download.py, received_files/download_record.py).

Equipe da Canoa -- 2026
mgd 2026-08-13
"""

from werkzeug.exceptions import default_exceptions

from .ups_handler import ups_handler
from .app_error_assistant import AppStumbled


def abort_handler(task_code: int, e: Exception, http_status_code: int) -> None:
    """
    Logs the error via ups_handler, then raises the HTTPException so the app-wide
    error handlers (see carranca/__init__.py) render the styled HTTP-error page.
    It raises before send_file() builds any response, so no download stream is
    ever started: the browser just shows the error page in the download tab.

    The route's own message travels as `ui_tech_msg`, shown in the page's technical
    box under the generic HTTP-<code> text. Werkzeug's `description` can't carry
    that signal: it is filled with an English default on every error.
    """
    ups_handler(task_code, str(e), e)
    tech = f"{e.msg} (Error Code: {e.error_code})" if isinstance(e, AppStumbled) else str(e)
    exc = default_exceptions[http_status_code](description=tech)
    exc.ui_tech_msg = tech  # read by _error_page() in carranca/__init__.py
    raise exc


# eof
