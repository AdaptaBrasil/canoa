"""
Equipe da Canoa -- 2024

Base shared objects

mgd 2024-10-01

"""

import json
from ..helpers.py_helper import as_bool, get_envvar, set_flags_from_argv


class Args:
    def __init__(self, as_debug):
        self.app_debug = as_debug
        self.app_mode = None  # Not ready, only flags
        self.display_debug = bool(as_debug)  # display debug, if in debug
        # verbose by default; silenced by env CANOA_DISPLAY_MUTE or the `--display_mute` argument
        # (`flask run` rejects unknown arguments, so on the server only the env var works)
        self.display_mute = as_bool(get_envvar("DISPLAY_MUTE", "false"))
        self.display_icons = True
        # FALSE: runtime messages keep going to the console and the log file.
        #        Only the debug lines depend on display_debug.
        # TRUE:  After start-up the server has a silent console and no log entries
        #        from the app for errors or validation steps.
        self.display_mute_after_init = False

    def __repr__(self):
        return json.dumps(self.__dict__, indent=None, separators=(",", ":"), sort_keys=True)

    def from_arguments(self):
        set_flags_from_argv(self)
        return self


# eof
