"""
Class for obfuscating an id/PK

A code is `(id + shift) * base + seed` written in base 36, so every code carries
letters and ends with the model's own seed digit. Decoding checks that digit: a
code made for one model (say a SEP) comes back as -1 from another (say a schema)
instead of pointing at a random row. The shift keeps the codes a few chars long.

Equipe da Canoa -- 2025
mgd 2026-11-12 base 36 + seed check digit (was: the seed as the base, digit-only codes)
"""

from ..helpers.py_helper import to_base


class IdToCode:
    base: int = 36  # digits 0-9 a-z, to_base()'s maximum
    shift: int = 1000  # ids are small, the shift gives 3+ chars
    invalid: str = "0"  # never produced by encode(): the smallest code is (0 + shift) * base + 1

    def __init__(self, seed: int):
        """
        seed: this model's check digit, 1 <= seed < base (each model has its own, see CanoaBase.__code_seed__)
        """
        if not (1 <= seed < IdToCode.base):
            raise ValueError(f"IdToCode seed must be in [1, {IdToCode.base - 1}], got {seed}.")
        self.seed = seed

    def decode(self, code: str) -> int:
        """
        Converts an obfuscated code string back to an integer ID; -1 when the code is
        invalid or was encoded with another seed.
        """
        if code == IdToCode.invalid:
            return -1

        try:
            raw = int(code, IdToCode.base)
        except (ValueError, TypeError):
            return -1

        if raw % IdToCode.base != self.seed:
            return -1
        return raw // IdToCode.base - IdToCode.shift

    def encode(self, id_value: int) -> str:
        """
        Generates an obfuscated code string from an ID.
        """
        if id_value < 0:
            return IdToCode.invalid
        return to_base((id_value + IdToCode.shift) * IdToCode.base + self.seed, IdToCode.base)


# eof
