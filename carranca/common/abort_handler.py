"""
abort_handler

    Shared except-block for the file-download routes (sep_ids_download.py,
    spd_download.py, received_files/download_record.py).

Equipe da Canoa -- 2026
mgd 2026-08-13
"""

from flask import g, abort

from .ups_handler import ups_handler
from .app_constants import APP_RAW_HTTP_ERROR_RAISED


def abort_handler(task_code: int, e: Exception, http_status_code: int) -> None:
    """
    Logs the error via ups_handler, then flags g.<APP_RAW_HTTP_ERROR_RAISED> so the
    app-wide error handlers (see carranca/__init__.py) skip their styled HTML page
    and let Werkzeug render its plain default instead -- an HTML error page here
    would corrupt the binary download stream. Direct abort() is required for the
    same reason; do not replace it with the project's usual ups_handler page unless
    the download mechanism itself is redesigned.
    """
    ups_handler(task_code, str(e), e)
    setattr(g, APP_RAW_HTTP_ERROR_RAISED, True)
    abort(http_status_code, description=str(e))


# eof
