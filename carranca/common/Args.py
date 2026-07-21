"""
 Equipe da Canoa -- 2024

 Base shared objects

 mgd 2024-10-01

 """

import json
from ..helpers.py_helper import set_flags_from_argv

class Args:
    def __init__(self, as_debug):
        self.app_debug = as_debug
        self.app_mode = None  # Not ready, only flags
        self.display_mute = not as_debug
        self.display_all = as_debug
        self.display_debug = as_debug
        self.display_icons = True
        self.display_mute_after_init = False

    def __repr__(self):
        return json.dumps(self.__dict__, indent=None, separators=(",", ":"), sort_keys=True)

    # 2026-07-20 dead code, no callers
    # @classmethod
    # def ignite(cls, json_str):
    #     data = json.loads(json_str)
    #     obj = cls(data.get("app_debug", False))
    #     obj.__dict__.update(data)
    #     return obj

    def from_arguments(self):
        set_flags_from_argv(self)
        return self


# eof
