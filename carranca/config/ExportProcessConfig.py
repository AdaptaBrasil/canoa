"""
ExportProcessConfig.py

Export process configurations class


Equipe da Canoa -- 2025
mgd

"""

# cSpell:ignore

from os import path
from ..private.IdToCode import IdToCode
from ..helpers.py_helper import UsualDict, now
from ..helpers.types_helper import OptListOfStr
from ..helpers.file_helper import folder_must_exist
from ..common.app_context_vars import sidekick, app_user


class ExportProcessConfig:
    _debug_process = None  # None -> set by param debug (see flag_debug)
    version = "0.1"
    folder = "exported-data"
    path = None
    # see json.dumps
    json = {"ensure_ascii": False, "indent": 0}

    _header = None
    _full_file_name = None
    _started = None
    _scm_cols = ["name", "color", "title", "v_sep_count", "ui_order"]
    _sep_cols = ["name", "description", "icon_svg", "icon_file_name", "ui_order"]
    scm_cols = []
    sep_cols = []
    coder: IdToCode

    def __init__(self, scm_cols: OptListOfStr=[], sep_cols: OptListOfStr= []):
        self.scm_cols = scm_cols.copy() if scm_cols else ExportProcessConfig._scm_cols.copy()
        self.sep_cols = sep_cols.copy() if sep_cols else ExportProcessConfig._sep_cols.copy()
        self._started = now()
        self.path = path.join(sidekick.config.COMMON_PATH, ExportProcessConfig.folder)
        self.coder = IdToCode(7)  #  obfuscate PKs when sent to UI
        if not folder_must_exist(self.path):
            raise Exception("No output folder")

    @property
    def full_file_name(self):
        if not self._full_file_name:
            _file = f"canoa_data-{self._started:%Y-%m-%d}.json"
            self._full_file_name = path.join(self.path, _file)

        return self._full_file_name

    @property
    def header(self) -> UsualDict:
        if not self._header:
            self._header = {
                "version": self.version,
                "when": self._started.isoformat(),
                "user": app_user.name,
                "decoding": "Base64 -> UTF-8",
            }

        return self._header


# eof
