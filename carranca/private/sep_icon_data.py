"""
SEP Edition, icon data content

Equipe da Canoa -- 2025
"""

import re
from os.path import splitext
from dataclasses import dataclass
from werkzeug.datastructures import FileStorage

from .sep_icon import ICON_MIN_SIZE
from .SepIconMaker import SepIconMaker
from ..models.private import Sep
from ..helpers.py_helper import crc16


@dataclass
class IconData:
    storage: FileStorage = None
    sent: bool = False
    file_name: str = ""
    is_svg: bool = False
    # set get_icon_data
    content: str = ""
    ready: bool = False
    crc: int = 0
    error_hint: str = ""
    error_code: int = 0


def get_icon_data(sep_row: Sep, icon_data: IconData) -> IconData:
    def __find(pattern: str, data: str) -> int:
        match = re.search(pattern, data, re.IGNORECASE | re.DOTALL)
        return match.start() if match else -1

    expected_ext = f".{SepIconMaker.ext}".lower()

    if not icon_data.sent:
        pass
    elif not splitext(icon_data.file_name)[1].lower().endswith(expected_ext):
        icon_data.error_hint = expected_ext
        icon_data.error_code = 1
    elif not icon_data.is_svg:
        icon_data.error_hint = expected_ext
        icon_data.error_code = 2
    elif len(data := icon_data.storage.read().decode("utf-8").strip()) < ICON_MIN_SIZE:
        icon_data.error_hint = f"≤ {ICON_MIN_SIZE}"
        icon_data.error_code = 3
    elif (start := __find(r"<svg.*?>", data)) < 0:
        icon_data.error_hint = "¿<svg>"
        icon_data.error_code = 4
    elif (end := __find(r"</svg\s*>", data)) < 0:
        icon_data.error_hint = "</svg>?"
        icon_data.error_code = 5
    elif (end - start) < ICON_MIN_SIZE:
        icon_data.error_hint = f"< {ICON_MIN_SIZE}"
        icon_data.error_code = 6
    elif not (sep_row.icon_svg or "") == (data or ""):
        icon_data.content = data
        icon_data.crc = crc16(data)
        icon_data.ready = True

    return icon_data


# eof
