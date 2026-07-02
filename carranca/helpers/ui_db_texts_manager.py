"""
Equipe da Canoa -- 2024

ui_db_texts_Helper.py
Retrieve UI texts items, for current user language, from tha DB

mgd 2024-04-03

TODO:
    - remove sections `secSuccess` & `secError`, just add the items on is on
      section. They will be loaded always
    - create a secCache for alway need msg, loaded on start. eg
        ui_datetime =

"""

# cSpell:ignore getDictResultset connstr adaptabrasil mgmt
from flask import current_app
from flask_login import current_user

from typing import Optional, Tuple, Any, cast
from .pw_helper import is_anyone_logged
from .py_helper import is_str_none_or_empty, clean_text
from .types_helper import DB_Texts, DB_Lookup, UI_Texts_Cache_Key
from ..common.UIDBTexts import UIDBTexts, CACHE_UI_TEXTS
from ..common.UITextsKeys import UITextsKeys
from ..common.app_constants import APP_LANG

# === Global 'constants' for HTML ui flask forms =============
from .. import global_ui_texts_cache

# ==== UI Texts Constants ====================================
Cache_Key = UI_Texts_Cache_Key

# use the default message key. eg ui_db_texts.set_msg_info(MSG_DEFAULT, time_info) MSG_DEFAULT -> 'msgInfo'
MSG_DEFAULT: str = ""


class UITexts_TableSearch:
    _LAST_UPDATE_KEY = "last_update"
    _CACHE_INTERNAL_INFO_KEY: Cache_Key = (" ", "mgmt_data", "key")
    ## TODO SAVE is Cache _CACHE_INTERNAL_INFO_KEY
    ## _cfg_cache_lifetime_min = int(current_app.config.get("APP_UI_DB_TEXTS_CACHE_LIFETIME_MIN", 0))

    def __init__(self, locale: str, section: str, item: Optional[str] = None):
        self.locale = locale
        self._locale = self.locale.lower()
        # avoid a " " section (see CACHE_INTERNAL_INFO_KEY)
        self.section = section.strip().lower()
        self.item = item.lower() if item else None
        self.value_is_str = self.item is not None
        self.value_is_dict = self.item is None

    def exists(self) -> bool:
        return self.as_tuple in global_ui_texts_cache

    def update(self, texts: DB_Texts | str) -> None:
        global_ui_texts_cache[self.as_tuple] = texts
        # TODO global_ui_texts_cache.update(self.as_tuple, texts)

    def get_text(self) -> DB_Texts | str | None:
        if not self.exists():
            return None
        value: dict | str = global_ui_texts_cache[self.as_tuple]
        return cast(dict, value).copy() if self.value_is_dict else value

    def set_info(self, key: str, info: Any) -> None:
        cache_info = self.get_info_value()
        cache_info[key] = info
        global_ui_texts_cache[UITexts_TableSearch._CACHE_INTERNAL_INFO_KEY] = cache_info

    def get_info_value(self) -> dict:
        cache_value = global_ui_texts_cache.get(UITexts_TableSearch._CACHE_INTERNAL_INFO_KEY, {})
        return cast(dict, cache_value)

    @property
    def as_tuple(self) -> Cache_Key:
        """Returns a tuple of all three 'indexed' attributes.
        If item is None, the entry contains a dict, else a str.
        """
        return (self.section, self._locale, self.item)


class MsgNotFound:
    cache: Optional[str] = None
    default = "The message with key '{0}' was not found in §: {1}."


# === Cache control ==========================================
def clear_ui_texts_cache() -> int:
    """
    The 'rope': empties every UI-text cache so DB text edits are picked up
    without restarting Canoa. Clears:
    - global_ui_texts_cache (get_section() / db_retrieve_text())
    - UIDBTexts.CACHE_UI_TEXTS (UIDBTexts._retrieve_value(), eg. ui_datetime, keyNotFound)
    - MsgNotFound.cache

    Returns the number of entries removed (handy for a log line).
    """
    count = len(global_ui_texts_cache) + len(CACHE_UI_TEXTS)
    global_ui_texts_cache.clear()
    CACHE_UI_TEXTS.clear()
    MsgNotFound.cache = None
    return count


# === current user's locale  ================================
def ui_texts_locale() -> str:
    locale = current_user.lang if is_anyone_logged() else APP_LANG
    return locale


# === SQL Constructor =======================================
def __get_ui_texts_query(cols: str, table_search: UITexts_TableSearch) -> str:
    # returns Select query for locale, section and, eventually, for only one item.
    # Use SQL lower(item) is better than item.lower because uses db locale.
    optional_item_filter = "" if table_search.item is None else f" and (item_lower = lower('{table_search.item}'))"

    # ** ⚠️ ******************************************************************
    #  don't use <schema>.table_name. Must set
    #  ALTER ROLE canoa_connstr IN DATABASE adaptabrasil SET search_path=canoa;
    query = (
        f"select {cols} from vw_ui_texts "
        f"where "
        f"(locale = lower('{table_search.locale}')) and (section_lower = lower('{table_search.section}')){optional_item_filter} "
        f"order by 1;"  # help debugging
    )
    return query


# === Data Retrievers =======================================
def __get_table_row(table_search: UITexts_TableSearch) -> Tuple[str, str]:
    """returns tuple(text, title) for the item/section pair"""
    from .db_helper import retrieve_rows

    query = __get_ui_texts_query("text, title", table_search)
    result = retrieve_rows(query)
    return ("", "") if not result else result


def _get_query_as_dict(query) -> DB_Texts:
    """returns DBTexts for the item/section pair"""
    from .db_helper import retrieve_dict

    db_texts = retrieve_dict(query)
    return db_texts


# === TODO use cache  ========================================
def _msg_not_found() -> str:  ## THIS IS OUTDATED ##
    if MsgNotFound.cache:
        return MsgNotFound.cache

    mnf = MsgNotFound.default
    try:
        text = db_retrieve_text("messageNotFound", UITextsKeys.Section.error)
        # 2026.03.27 text, _ = __get_table_row("messageNotFound", UITextsKeys.Section.error)
        MsgNotFound.cache = MsgNotFound.default if is_str_none_or_empty(text) else text
        mnf = MsgNotFound.cache
    except:
        pass

    return mnf


# Cached Texts retrievers ==================================
def get_section(section_name: str) -> DB_Texts:
    """
    returns a DBTexts of the 'section_name' from table vw_ui_texts
    """
    if is_str_none_or_empty(section_name):
        return {}

    table_cache = UITexts_TableSearch(ui_texts_locale(), section_name)

    if table_cache.exists():
        return cast(DB_Texts, table_cache.get_text())
    else:  # not in cache, retrieve section
        query = __get_ui_texts_query("item, text", table_cache)
        items = _get_query_as_dict(query) or {}
        # TODO: raise if section does not
        # if len(items) == 0:
        #     raise KeyError(f"UI texts section '{section_name}' for [{table_cache.locale}] not found or has no items.")
        items.update({UITextsKeys.Section.name: section_name})
        items.update({UITextsKeys.Form.user_locale: table_cache.locale})

        _glb = {key: value for key, value in current_app.jinja_env.globals.items() if isinstance(value, str)}
        items.update(_glb)

        table_cache.update(items)

        return items.copy()  # Ensures caller gets a copy, preventing cache pollution


def db_retrieve_text(item: str, section: str, default: str | None = None) -> str:
    """
    returns text for the item/section pair. if not found, a `warning message`
    """
    table_search = UITexts_TableSearch(ui_texts_locale(), section, item)
    if table_search.exists():
        text = table_search.get_text()
        return cast(str, text if isinstance(text, str) else "")

    text, _ = __get_table_row(table_search)

    if not is_str_none_or_empty(text):
        # only use HTML control chars, 2026.03.28
        text = clean_text(text)
    elif default is None:
        text = _msg_not_found().format(item, section)
    else:
        text = default

    table_search.update(text)

    return text


# Texts retrievers helpers ==================================


# TODO Change this get/set by UIDBTexts
def get_app_menu() -> DB_Texts:
    db_texts = get_section("appMenu")
    return db_texts


def get_db_texts(section_name: str) -> DB_Texts:
    db_texts = get_section(section_name)
    # 2026/03/18 db_texts SHOULD have is on msgSuccess, msgError, ... they are reallocated (to ._msg dict) just before sending to ui
    # see carranca\common\UIDBTexts.py
    # if db_texts:
    #     for k in [
    #         UITextsKeys.Msg.success,
    #         UITextsKeys.Msg.warn,
    #         UITextsKeys.Msg.error,
    #         UITextsKeys.Msg.fatal,
    #         UITextsKeys.Msg.display_msg_only,
    #     ]:
    #         if k in db_texts:  # DEBUG
    #             print(f"Unexpected item en section {section_name}: {k}.")
    return db_texts


def init_ui_db_texts(ui_db_section: str) -> UIDBTexts:
    from ..common.app_context_vars import sidekick

    db_texts = get_db_texts(ui_db_section) if ui_db_section else {}
    ## add to ui_db_texts useful values  of 'general use'
    ui_dt_format = sidekick.config.APP_UI_DATETIME_FORMAT
    db_lookup = cast(DB_Lookup, db_retrieve_text)
    ui_db_texts = UIDBTexts(db_texts, sidekick.debugging, ui_dt_format, db_lookup)

    return ui_db_texts


# eof
