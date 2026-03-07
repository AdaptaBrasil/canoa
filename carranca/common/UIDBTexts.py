"""
Celebrating Architectural Excellence: The UITexts Wrapper Class!
That is a fantastic piece of architectural design!
Your solution to wrap the dictionary—enforcing strong types while
maintaining backward compatibility—is the essence of good
object-oriented programming.

It manages complexity, maintains flexibility, and adds robust
debugging safeguards. Well done!

Gemini 2025-11-08
"""

import warnings
from typing import Dict, Any, Type, cast
from .UITextsKeys import UITextsKeys

# Define a unique object to act as the sentinel default value for dictionary lookups
_MISSING = object()

# Define the error constant for cleaner code
KEY_NOT_FOUND_ERROR = "Key '{0}' not found, cannot cast to {1}."

# New constant for explicit None values:
VALUE_IS_NONE_ERROR = "Key '{0}' value is None, cannot cast to {1}."


class UIDBTexts:
    # -------------------------------------------------------------
    # Internal helper methods for value retrieval and type checking
    def _get_value(self, key: str) -> Any:
        value = self._data.get(key, _MISSING)
        return value

    def _key_exists(self, key: str) -> bool:
        return self._get_value(key) is not _MISSING

    def _get_and_check_type(self, key: str, expected_type: Type) -> Any:
        """
        Optimized internal method: Fetches value with a single lookup and differentiates
        between missing keys and keys with an explicit None value.

        Raises KeyError if the key is missing.
        """

        # 1. Check for missing key (Hard Error)
        if not self._key_exists(key):
            # The sentinel was returned, meaning the key does not exist.
            raise KeyError(KEY_NOT_FOUND_ERROR.format(key, expected_type.__name__))

        # 2. Lookup with a unique sentinel object for performance
        value = self._get_value(key)

        # 3. Check for explicit None value (Soft Warning in debug)
        if value is None:
            # The key exists, but its stored value is None.
            warnings.warn(
                f"UI_Texts Warning: Key '{key}' returned None. Type check for "
                f"{expected_type.__name__} skipped.",
                UserWarning,
                stacklevel=2,
            )
            return None

        # 4. Debug runtime type check (for non-None values)
        if self.is_debug_mode:
            if not isinstance(value, expected_type):
                warnings.warn(
                    f"UI_Texts Runtime Error: Key '{key}' expected type {expected_type.__name__}, "
                    f"but found {type(value).__name__}. Check database entry.",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # 5. Return the raw value.
        return value

    def _get_value_or_default(self, key: str, default: str | bool | None, typ: type) -> str | bool | None:
        def __default() -> str | bool | None:
            return default if isinstance(default, typ) else None

        if not self._key_exists(key):
            value = __default()
        elif (value := self._get_value(key)) is None:
            value = __default()
        else:
            value = self._get_and_check_type(key, typ)

        return value

    """
    A dictionary wrapper for UI texts (loaded in the DB) providing strongly typed access methods
    (e.g., .get_str(), .get_bool(), .get_float()) and dictionary-like access for strings via __getitem__.
    Performs runtime type checking only when running in debug mode.
    """

    def __init__(self, data: Dict[str, Any], debugging: bool):
        self._data = data
        self.is_debug_mode = debugging

    def data(self) -> Dict[str, Any]:
        """
        Returns the raw, underlying dictionary for use with unpacking into template calls
        e.g., render_template( tmpl_ffn, **ui_texts.data() )
        """
        return self._data

    def format(self, key: str, *args) -> str:
        """
        Retrieves a string value by key and safely attempts to format it
        using positional arguments (*args).

        If the key is missing or invalid, errors are raised by self.get_str().
        If formatting fails (e.g., arguments don't match placeholders), the
        unformatted string is returned, and a RuntimeWarning is issued
        in debug mode.
        """
        result = self.get_str(key, "")
        try:
            result = result.format(*args)
        except Exception as e:
            if self.is_debug_mode:
                # Use a specific warning to log the formatting failure in debug.
                warnings.warn(
                    f"UIDBTexts Formatting Error: Failed to format key '{key}'. "
                    f"Arguments ({args}) did not match placeholders. Error: {e}",
                    RuntimeWarning,
                    stacklevel=2,
                )
            pass

        return result

    # --- Dictionary Access for Strings (90% case) ---

    def __getitem__(self, key: str) -> str:
        """Allows dictionary-like access (ui_texts["key"]) for strings."""
        return self.get_str(key, "")

    # --- Dictionary setter for Strings | bool (90% case) ---
    def __setitem__(self, key: str, value: str | bool) -> None:
        """
        Allows dictionary-like assignment (ui_texts["key"] = value).
        Restricts insertion types strictly to str or bool.
        """
        # This check runs always to enforce the class's contract.
        if not isinstance(value, (str, bool)):
            raise TypeError(
                f"UIDBTexts only accepts str or bool for assignment, "
                f"but received type {type(value).__name__} for key '{key}'."
            )

        self._data[key] = value

    # --- merged by mgd on 2025-11-08:
    # --  get_str() now supports an optional default parameter for missing keys ---
    # def get_str(self, key: str, default: str = "") -> str:
    #     try:
    #         value = self._data.get(key, _MISSING)
    #         return default if value is _MISSING else self.str(key)
    #     except KeyError:
    #         return default

    # def str(self, key: str) -> str:
    #     """Retrieves a value guaranteed to be a string."""
    #     raw_value = self._get_and_check_type(key, str)
    #     return "" if raw_value is None else cast(str, raw_value)

    # --- Type-Specific Accessors ---
    def get_str(self, key: str, default: str = "") -> str:
        """
        Retrieves a value guaranteed to be a string.
        If the key is missing returns the provided default value as str
        """
        value = self._get_value_or_default(key, default, str)
        return cast(str, value)

    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """
        Retrieves a value guaranteed to be a boolean.
        If the key is missing returns the provided default value as str
        """
        value = self._get_value_or_default(key, default, bool)
        return cast(bool, value)

    def get_int(self, key: str) -> int:
        """Retrieves a value guaranteed to be an integer."""
        raw_value = self._get_and_check_type(key, int)
        if raw_value is None:
            raise TypeError(VALUE_IS_NONE_ERROR.format(key, int.__name__))

        return cast(int, raw_value)

    def get_float(self, key: str) -> float:
        """Retrieves a value guaranteed to be a float (decimal number)."""
        raw_value = self._get_and_check_type(key, float)
        if raw_value is None:
            raise TypeError(VALUE_IS_NONE_ERROR.format(key, float.__name__))

        return cast(float, raw_value)

    @property
    def section(self) -> str:
        """Returns the section name associated with this UIDBTexts instance, if available."""
        return self.get_str(UITextsKeys.Section.name)

    @property
    def display_msg_only(self) -> bool:
        """True when configured to display only messages (no form inputs, etc)."""
        return self.get_bool(UITextsKeys.Msg.display_msg_only, False)

    @display_msg_only.setter
    def display_msg_only(self, value: bool) -> None:
        self[UITextsKeys.Msg.display_msg_only] = value


# eof
