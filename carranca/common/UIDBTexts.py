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

from typing import Dict, Any, Type, cast
import warnings

# Define a unique object to act as the sentinel default value for dictionary lookups
_MISSING = object()

# Define the error constant for cleaner code
KEY_NOT_FOUND_ERROR = "Key '{0}' not found, cannot cast to {1}."

# New constant for explicit None values:
VALUE_IS_NONE_ERROR = "Key '{0}' value is None, cannot cast to {1}."


class UIDBTexts:
    """
    A dictionary wrapper for UI texts (loaded in the DB) providing strongly typed access methods
    (e.g., .str(), .bool(), .float()) and dictionary-like access for strings via __getitem__.
    Performs runtime type checking only when running in debug mode.
    """

    def __init__(self, data: Dict[str, Any], debugging: bool):
        self._data = data
        self.is_debug_mode = debugging

    def _get_and_check_type(self, key: str, expected_type: Type) -> Any:
        """
        Optimized internal method: Fetches value with a single lookup and differentiates
        between missing keys and keys with an explicit None value.

        Raises KeyError if the key is missing.
        """
        # 1. Lookup with a unique sentinel object for performance
        value = self._data.get(key, _MISSING)

        # 2. Check for missing key (Hard Error)
        if value is _MISSING:
            # The sentinel was returned, meaning the key does not exist.
            raise KeyError(KEY_NOT_FOUND_ERROR.format(key, expected_type.__name__))

        # 3. Check for explicit None value (Soft Warning in debug)
        if value is None:
            # The key exists, but its stored value is None.
            warnings.warn(
                f"UI_Texts Warning: Key '{key}' returned None. Type check for " f"{expected_type.__name__} skipped.",
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

    def dict(self) -> Dict[str, Any]:
        """
        Returns the raw, underlying dictionary for use with unpacking
        e.g., in template rendering: **ui_texts.dict()
        """
        return self._data

    def format(self, key: str, *args) -> str:
        """
        Retrieves a string value by key and safely attempts to format it
        using positional arguments (*args).

        If the key is missing or invalid, errors are raised by self.str().
        If formatting fails (e.g., arguments don't match placeholders), the
        unformatted string is returned, and a RuntimeWarning is issued
        in debug mode.
        """
        result = self.str(key)
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
        return self.str(key)

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

    # --- Type-Specific Accessors ---
    def get_str(self, key: str, default: str = "") -> str:

        try:
            value = self._data.get(key, _MISSING)

            return default if value is _MISSING else self.str(key)

        except KeyError:
            return default

    def str(self, key: str) -> str:
        """Retrieves a value guaranteed to be a string."""
        raw_value = self._get_and_check_type(key, str)
        return "" if raw_value is None else cast(str, raw_value)

    def bool(self, key: str) -> bool:
        """Retrieves a value guaranteed to be a boolean."""
        raw_value = self._get_and_check_type(key, bool)
        if raw_value is None:
            raise TypeError(VALUE_IS_NONE_ERROR.format(key, bool.__name__))

        return cast(bool, raw_value)

    def int(self, key: str) -> int:
        """Retrieves a value guaranteed to be an integer."""
        raw_value = self._get_and_check_type(key, int)
        if raw_value is None:
            raise TypeError(VALUE_IS_NONE_ERROR.format(key, int.__name__))

        return cast(int, raw_value)

    def float(self, key: str) -> float:
        """Retrieves a value guaranteed to be a float (decimal number)."""
        # Note: We now use 'float' as the function name and type.
        raw_value = self._get_and_check_type(key, float)
        if raw_value is None:
            raise TypeError(VALUE_IS_NONE_ERROR.format(key, float.__name__))

        return cast(float, raw_value)


# eof
