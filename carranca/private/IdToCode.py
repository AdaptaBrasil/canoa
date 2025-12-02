"""
Class for obfuscating an id/PK


Equipe da Canoa -- 2025
mgd
"""

from typing import Optional
from ..helpers.py_helper import to_base


class IdToCode:
    # This class attribute can serve as a default or for other static uses if any arise.
    base: int = 9
    shift: int = 7
    invalid: str = "0"

    def __init__(self, instance_base: int = 13, instance_shift: int = 6):
        """
        Initializes the IdToCode instance with a specific base for encoding/decoding.
        """
        self.base = instance_base
        self.shift = instance_shift

    def decode(self, code: str) -> int:
        """
        Converts an obfuscated code string back to an integer ID, using the instance's base.
        """
        if code == IdToCode.invalid:
            return -1

        try:
            raw = int(code, self.base)
            decoded_id = raw // self.base - self.shift
        except (ValueError, TypeError):
            decoded_id = -1
        return decoded_id

    def encode(self, id_value: int) -> str:
        """
        Generates an obfuscated code string from an ID, using the instance's base.
        """
        return IdToCode.invalid if id_value < 0 else to_base(self.base * (id_value + self.shift), self.base)


# eof
