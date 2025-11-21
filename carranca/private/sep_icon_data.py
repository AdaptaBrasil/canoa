"""
SEP Edition, icon data content

Equipe da Canoa -- 2025
"""

import re
from flask import request
from os.path import splitext
from dataclasses import dataclass
from werkzeug.datastructures import FileStorage

from .sep_icon import ICON_MIN_SIZE
from .SepIconMaker import SepIconMaker
from ..models.private import Sep
from ..helpers.py_helper import crc16


@dataclass
class IconData:
    content: str = ""
    file_name: str = ""
    ready: bool = False
    crc: int = 0
    error_hint: str = ""
    error_code: int = 0


@dataclass
class IconInfo:
    sent: bool = False
    storage: FileStorage = None
    file_name: str = ""


def get_icon_data(sep_row: Sep, icon_info: IconInfo, icon_name) -> IconData:
    def __find(pattern: str, data: str) -> int:
        match = re.search(pattern, data, re.IGNORECASE | re.DOTALL)
        return match.start() if match else -1

    icon_data = IconData(file_name=icon_info.file_name)
    expected_ext = f".{SepIconMaker.ext}".lower()

    if not icon_info.sent:
        pass
    elif not splitext(icon_data.file_name)[1].lower().endswith(expected_ext):
        icon_data.error_hint = expected_ext
        icon_data.error_code = 1
    elif not (file_obj := request.files.get(form.icon_filename.name)):
        icon_data.error_hint = "↑×"
        icon_data.error_code = 2
    elif len(data := file_obj.read().decode("utf-8").strip()) < ICON_MIN_SIZE:
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
