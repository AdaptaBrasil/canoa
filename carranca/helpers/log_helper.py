"""
Flask's Log interface

Equipe da Canoa -- 2025
mgd 2025-03-14
"""

import logging
from os import path
from flask import Flask
from typing import Tuple
from logging.handlers import RotatingFileHandler

from .py_helper import is_str_none_or_empty
from .user_helper import get_unique_filename
from .file_helper import folder_must_exist


# ---------------------------------------------------------------------------- #
def do_log_file(
    app: Flask,
    file_name: str = "",
    file_folder: str = "",
    min_level: int = logging.INFO,
) -> Tuple[str, str, str]:

    msg_error = ""
    full_name = ""
    s_level = logging.NOTSET

    # https://www.adventuresinmachinelearning.com/flask-logging-the-ultimate-guide-for-developers/
    task = "file_name"
    try:
        if is_str_none_or_empty(file_name):
            file_name = get_unique_filename(f"{app.name}_", ".log")

        task = "file_folder"
        if is_str_none_or_empty(file_folder):
            file_folder = "log_files"

        if not folder_must_exist(file_folder):
            msg_error = f"Cannot create log's files folder [{file_folder}]."
        else:
            task = "full_name"
            full_name = path.join(".", file_folder, file_name)

            task = "level"
            s_level = logging._levelToName[min_level]

            task = "handler"
            handler = RotatingFileHandler(full_name, maxBytes=10000, backupCount=1, encoding="utf-8")
            handler.setLevel(min_level)
            app.logger.addHandler(handler)
    except Exception as e:
        msg_error = f"Cannot create log's {task}: [{e}]"

    return msg_error, full_name, s_level


# eof
