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

import re
import json
import warnings
from typing import Optional, Dict, Any, Type, List, cast
from datetime import datetime, timedelta
from .UITextsKeys import UITextsKeys
from ..helpers.py_helper import camel_to_snake
from ..helpers.types_helper import DB_Lookup, DB_Texts, DB_Texts_Args


# Define a unique object to act as the sentinel default value for dictionary lookups
_MISSING = object()

# Define the error constant for cleaner code
KEY_NOT_FOUND_ERROR = "Key '{0}' not found, cannot cast to {1}."

# New constant for explicit None values:
VALUE_IS_NONE_ERROR = "Key '{0}' value is None, cannot cast to {1}."

# Do the best to display the msg {0} to the user & give some tech info
KEY_NOT_FOUND_MSG = "<b>{0}</b><br><small>The message with key '{1}' was not found in §:&nbsp;{2}.</small>"

CACHE_UI_TEXTS: DB_Texts = {}


# User Interface Database Texts
class UIDBTexts:
    # -------------------------------------------------------------
    # Internal helper methods for value retrieval and type checking
    def _get_value(self, key: str) -> Any:
        value = self._data.get(key, _MISSING)
        return None if value is _MISSING else value

    def _key_exists(self, key: str) -> bool:
        value = self._data.get(key, _MISSING)
        return value is not _MISSING

    def _get_and_check_type(self, key: str, expected_type: Type) -> Any:
        """
        Optimized internal method: Fetches value with a single lookup and differentiates
        between missing keys and keys with an explicit None value.

        Raises KeyError if the key is missing.
        """
        from ..common.app_context_vars import sidekick

        # 1. Check for missing key (Hard Error)
        if not self._key_exists(key):
            # The sentinel was returned, meaning the key does not exist.
            raise KeyError(KEY_NOT_FOUND_ERROR.format(key, expected_type.__name__))

        # 2. Lookup with a unique sentinel object for performance
        value = self._get_value(key)

        def __warn(text: str):
            sidekick.display.error(text)
            warnings.warn(text, UserWarning, stacklevel=2)
            return

        # 3. Check for explicit None value (Soft Warning in debug)
        if value is None:
            # The key exists, but its stored value is None.
            __warn(f"UI_Texts Warning: Key '{key}' returned None. Type check for " f"{expected_type.__name__} skipped.")
            return None

        # 4. Debug runtime type check (for non-None values)
        if self.is_debug_mode:
            if not isinstance(value, expected_type):
                __warn(
                    f"UI_Texts Runtime Error: Key '{key}' expected type {expected_type.__name__}, "
                    f"but found {type(value).__name__}. Check database entry.",
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

    def _retrieve_value(self, key: str, section: str, default: str = "", cache_it: bool = False) -> str:
        # TODO missing lng
        cache_key = f"{section}={key}"

        cached = CACHE_UI_TEXTS.get(cache_key, _MISSING)
        if cached is not _MISSING:
            return cast(str, cached)
        elif self._db_lookup is None:
            value = default
        else:
            value = self._db_lookup(key, section, default)
            if cache_it:  # if value == default, => cache it, no need to access the DB again.
                CACHE_UI_TEXTS.update({cache_key: value})

        return value

    def _get_ui_datetime(self) -> str:
        ui_dt_str = self._retrieve_value("ui_datetime", UITextsKeys.Section.success, self.ui_dt_format, True)
        return ui_dt_str

    """
    A dictionary wrapper for UI texts (loaded in the DB) providing strongly typed access methods
    (e.g., .get_str(), .get_bool(), .get_float()) and dictionary-like access for strings via __getitem__.
    Performs runtime type checking only when running in debug mode.
    """

    def __init__(
        self, data: Dict[str, Any], debugging: bool, ui_dt_format: str = "", db_lookup: DB_Lookup | None = None
    ):
        # collect msg keys names
        items = UITextsKeys.Msg.__dict__.items()
        self._msg_keys = [value for key, value in items if not key.startswith("__")]

        # filter all msg to _msg dict
        self._msg = {k: v for k, v in data.items() if k in self.msg_keys}
        # filter get all 'texts' into _data dict
        self._data = {k: v for k, v in data.items() if k not in self.msg_keys}

        self.is_debug_mode = debugging
        self.ui_dt_format = ui_dt_format if ui_dt_format else "YYYY-MM-DD HH:MM"
        self._db_lookup = db_lookup
        self.__section__ = self.get_str(UITextsKeys.Section.name)
        self._data.pop(UITextsKeys.Section.name, None)

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

    def __len__(self) -> int:
        return len(self._data)

    # --- Update dict values ---
    def update_info_msg(self, *args) -> str:
        return self.update_item(UITextsKeys.Msg.info, *args)

    def set_value(self, key: str, value: str) -> str:
        """
        Replace the item with new value
        """
        self[key] = value
        return value

    def update_item(self, key: str, *args) -> str:
        """
        Updates the ._data dictionary value
        """
        value = self.format(key, *args)
        self.set_value(key, value)
        return value

    def replace(self, key: str, from_key, *args) -> str:
        """
        replace item's value from other item (with key from_key)
        """
        value = self.format(from_key, *args)
        self.set_value(key, value)
        return value

    # --- Type-Specific Accessors ---
    def get_msg(self, key: str, default: str = "") -> str:
        """
        Retrieves a value from self._msg guaranteed to be a string.
        """
        _value = self._msg.get(key, _MISSING)
        value = default if _value is _MISSING else str(_value)
        return value

    def get_str(self, key: str, default: str = "") -> str:
        """
        Retrieves a value from self._data guaranteed to be a string.
        If the key is missing returns the provided default value as str
        """
        value = self._get_value_or_default(key, default, str)
        return cast(str, value)

    def get_bool(self, key: str, default: bool | None = None) -> bool:
        """
        Retrieves a value from self._data guaranteed to be a boolean.
        If the key is missing returns the provided default value as str
        """
        value = self._get_value_or_default(key, default, bool)
        return cast(bool, value)

    def get_int(self, key: str) -> int:
        """Retrieves a value from self._data guaranteed to be an integer."""
        raw_value = self._get_and_check_type(key, int)
        if raw_value is None:
            raise TypeError(VALUE_IS_NONE_ERROR.format(key, int.__name__))

        return cast(int, raw_value)

    def get_float(self, key: str) -> float:
        """Retrieves a value from self._data guaranteed to be a float (decimal number)."""
        raw_value = self._get_and_check_type(key, float)
        if raw_value is None:
            raise TypeError(VALUE_IS_NONE_ERROR.format(key, float.__name__))

        return cast(float, raw_value)

    def reset_messages(self):
        """safely wipe all potential ui messages from the data dict."""
        for k_msg in self.msg_keys:
            self._data.pop(k_msg, None)

    # -- Message manipulation

    def get_ui_datetime(self, add_unit: int, dt_from: datetime, unit: str = "hours"):
        ui_dt_str = self._retrieve_value("ui_datetime", UITextsKeys.Section.success, self.ui_dt_format, True)
        value = self.set_ui_datetime("", ui_dt_str, add_unit, dt_from, unit)

        return value

    def set_ui_datetime(
        self,
        key: str,
        value: str,
        dt_to_or_add: datetime | int,
        dt_from: Optional[datetime] = None,
        unit: str = "hours",
        index: str = "days",
    ) -> str:
        """
        Tries is best to make a nice readable datetime msg
        Example used on code:
            value = '{"2": "depois de amanhã às %H:%M", "1": "amanhã às %H:%M", "0": "hoje às %H:%M", "-1": "ontem às %H:%M", "n": "%d/%m/%Y às %H:%M", "text": "válido até {0}."'
        """
        if not value:
            value = self.get_str(key)  # » '{"2": "depois de amanhã às %H:%M", "1": "amanhã às %H...

        if not dt_from:
            dt_from = datetime.now()

        if isinstance(dt_to_or_add, datetime):
            dt_to = dt_to_or_add
        else:
            add = int(dt_to_or_add)
            dt_to = dt_from + timedelta(**{unit: add})  # » add in a number in unit (eg hours)

        delta = dt_to.date() - dt_from.date()
        _qtd = {
            "days": delta.days,
            "hours": int(delta.total_seconds() / 3600),
            "minutes": int(delta.total_seconds() / 60),
            "seconds": int(delta.total_seconds()),
        }
        qtd = str(_qtd[index])  # » '2' [days] (example)

        dic: dict = json.loads(value)
        fallback = dic.get("n", self.ui_dt_format)  # » "%d/%m/%Y às %H:%M"
        qtd_frm = dic.get(qtd, fallback)  # » "depois de amanhã às %H:%M",

        qtd_txt = dt_to.strftime(qtd_frm)  # » "depois de amanhã às 11:37",
        text = dic.get("text", "{0}")  # » válido até {0}
        msg = text.format(qtd_txt)  # » válido até depois de amanhã às 11:37.
        if key in self.data():
            self[key] = msg
        return msg

    def try_recursive(self, key: str, value: str) -> str:
        """
        Replace all placeholders of the form {<key>_<suffix>} inside the given text.
        """

        _keys = re.findall(r"\{(" + key + r"_[^}]+)\}", value)
        if not _keys:
            return value

        replacements = {k: v for k in _keys if (v := self.get_str(k, ""))}

        result = value
        for k, v in replacements.items():
            result = result.replace("{" + k + "}", v)

        return result

    # def try_date_day(self, key: str, value: str) -> str:

    def _key_not_found_ui_msg(self, key: str, alternative_section: str) -> str:
        default = KEY_NOT_FOUND_MSG
        nice_key = camel_to_snake(key).replace("_", " ").capitalize()
        key_not_found_msg = self._retrieve_value("keyNotFound", UITextsKeys.Section.error, default, True)
        section = (
            self.section + "" if alternative_section == UITextsKeys.Section.current else f", {alternative_section}"
        )
        return key_not_found_msg.format(nice_key, key, section)

    def _set_or_add_msg(
        self, key: str, alternative_section: str, msg_kind: str, args: DB_Texts_Args = None
    ) -> tuple[str, str]:
        """Retrieves text (local or from DB) and adds it to a dictionary, formatted.

        args:
            key: The item identifier.
            section: The section identifier, see UITextsKeys.section
            msg_kind: The message kind, see UITextsKeys.Msg => [info, warn, error, success, fatal, tech]
            args: Optional arguments for formatting the retrieved text.

        Returns:
            The actual key used
            The formatted text.

        mgd 2025-10-30
        Check if texts contains the required item
        This will allow to set the items of sections [secSuccess, secError]
        in the 'current' section.

        """
        from ..common.app_context_vars import sidekick

        # take the default value for Item
        # Example:  (key = '') and (msg_kind = 'msgInfo') => key = msgInfo
        key = key or msg_kind

        # search in the messages dict of the UITextsKeys.Section.current section
        msg_text: str = self.get_msg(key)

        if not msg_text:
            # search in the items dict of the UITextsKeys.Section.current section
            msg_text = self.get_str(key)

        if len(self) == 0 and self.section:
            # TODO: ui_db_texts can have no items, the next error message mask this situation. TODO:
            sidekick.display.error(f"Error: ui_db_texts[{self.section}] has no items.")

        if msg_text or (alternative_section == UITextsKeys.Section.current):
            pass  # found (can be '') or we have no alternative section to search on
        else:  # search the DB in the alternative section (secError, secSuccess)
            msg_text = self._retrieve_value(key, alternative_section, "")

        try:
            if not msg_text:
                value = self._key_not_found_ui_msg(key, alternative_section)
            elif not args:
                value = msg_text
            elif isinstance(args, dict):
                value = msg_text.format(**args)
            elif isinstance(args, tuple):
                value = msg_text.format(*args)
            else:  # str
                value = msg_text.format(args)

            value = self.try_recursive(key, value)
        except Exception as e:
            sidekick.display.error(f"UIDBTexts, msg [{msg_text}] render error: [{e}].")
            value = msg_text

        if value:  # add or refresh
            self[msg_kind] = value

        return key, value

    def set_msg_success(self, key: str = "", args: DB_Texts_Args = None) -> tuple[str, str]:
        """
        returns used `key` and the retrieved `msg`
        Removes all other msg
        Retrieves `text` for the [item, <curr_section>] | [item, 'secSuccess'] pair
        (of the vw_ui_texts view)
        and adds the pair to `texts` => texts.add(text, 'msgSuccess')

        Finally sets ui_db_texts.Msg.display_msg_only = True, so the form only displays
        the message (no other form inputs)
        """

        self.reset_messages()
        key, msg = self._set_or_add_msg(key, UITextsKeys.Section.success, UITextsKeys.Msg.success, args)
        self.display_msg_only = True
        return key, msg

    def set_msg_fatal(self, key: str = "", args: DB_Texts_Args = None) -> tuple[str, str]:
        """
        returns used `key` and the retrieved `msg`
        Removes all other msg
        Retrieves `text` for the [item, <curr_section>] | [item, 'secError'] pair
        (of the vw_ui_texts view)
        and adds the pair to `texts` => texts.add(text, 'secError')

        Finally sets ui_db_texts.Msg.display_msg_only = True, so the form only displays
        the message (no other form inputs)
        """
        self.reset_messages()
        key, msg = self.set_msg_error(key or UITextsKeys.Msg.fatal, args)
        self.display_msg_only = True
        return key, msg

    def set_msg_error(self, key: str = "", args: DB_Texts_Args = None) -> tuple[str, str]:
        """returns used `key` and retrieved `msg`"""
        key, msg = self._set_or_add_msg(key, UITextsKeys.Section.error, UITextsKeys.Msg.error, args)
        return key, msg

    def set_msg_info(self, key: str = "", args: DB_Texts_Args = None) -> tuple[str, str]:
        """returns used `key` and retrieved `msg`
        Information texts can be shared with the success section ;—)
        """
        key, msg = self._set_or_add_msg(key, UITextsKeys.Section.success, UITextsKeys.Msg.info, args)
        return key, msg

    def set_msg_warn(self, key: str = "", args: DB_Texts_Args = None) -> tuple[str, str]:
        """returns used `key` and the retrieved `msg`
        Warning texts can be shared with the error section ;—)
        """
        key, msg = self._set_or_add_msg(key, UITextsKeys.Section.error, UITextsKeys.Msg.warn, args)
        return key, msg

    @property
    def msg_keys(self) -> List[str]:
        return self._msg_keys

    @property
    def section(self) -> str:
        """Returns the section name associated with this UIDBTexts instance, if available."""
        return self.__section__
        ## return self.get_str(UITextsKeys.Section.name)

    @property
    def display_msg_only(self) -> bool:
        """True when configured to display only messages (no form inputs, etc)."""
        return self.get_bool(UITextsKeys.Msg.display_msg_only, False)

    @display_msg_only.setter
    def display_msg_only(self, value: bool) -> None:
        self[UITextsKeys.Msg.display_msg_only] = value


# eof
