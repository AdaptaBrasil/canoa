"""
 Basic information of a user's SEP

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore MgmtSep

from ..helpers.py_helper import is_str_none_or_empty

ICON_MIN_SIZE = 60  # bytes


class SepData:
    from ..models.private import Sep

    def __init__(self, icon_url: str, sep_fullname: str, sep: Sep):
        self.icon_url = icon_url
        self.sep_fullname = sep_fullname
        self.sep = sep


# SEP's icon info
class SepIcon:
    def __init__(self, sep_data: SepData):
        from .SepIconMaker import SepIconMaker

        sep = sep_data.sep
        self.id = sep.id
        self.icon_url = sep_data.icon_url

        self.has_icon = not is_str_none_or_empty(sep.icon_file_name)
        self.icon_file_name = sep.icon_file_name

        self.icon_full_name = SepIconMaker.get_full_name(sep.icon_file_name) if self.has_icon else ""


# eof
