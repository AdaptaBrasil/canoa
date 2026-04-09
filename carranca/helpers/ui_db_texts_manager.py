"""
Equipe da Canoa -- 2024

ui_db_texts_Helper.py
Retrieve UI texts items, for current user language, from tha DB

mgd 2024-04-03

TODO:
    - remove sections `secSuccess` & `secError`, just add the items on is on
      section. They will be loaded always
    - create a secCache for alway need msg, loaded on start. eg
        ui_datatime =

"""

# cSpell:ignore getDictResultset connstr adaptabrasil mgmt
from flask import current_app
from flask_login import current_user

from typing import TypeAlias, Optional, Tuple, Any, cast
from .pw_helper import is_anyone_logged
from .py_helper import is_str_none_or_empty, clean_text
from .types_helper import DB_Texts, DB_Lookup
from ..common.UIDBTexts import UIDBTexts
from ..common.UITextsKeys import UITextsKeys
from ..common.app_constants import APP_LANG

# === Global 'constants' for HTML ui flask forms =============
from .. import global_ui_texts_cache  # it is used, ignore warn


# ==== UI Texts Constants ====================================
Cache_Key: TypeAlias = Tuple[str, str, Optional[str]]

# use the default message key. eg set_msg_info(MSG_DEFAULT, ui_db_texts, time_info) MSG_DEFAULT -> 'msgInfo'
MSG_DEFAULT: str = ""


class UITexts_TableSearch:
    global global_ui_texts_cache
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
        return cache_value

    @property
    def as_tuple(self) -> Cache_Key:
        """Returns a tuple of all three 'indexed' attributes.
        If item is None, the entry contains a dict, else a str.
        """
        return (self.section, self._locale, self.item)


class MsgNotFound:
    cache: Optional[str] = None
    default = "The message with key '{0}' was not found in §: {1}."


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
def __get_table_row(table_search: UITexts_TableSearch) -> tuple[str, str]:
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


def _set_or_add_msg(item: str, section: str, name: str, ui_db_texts: UIDBTexts, args: tuple | dict | None = None) -> str:
    """Retrieves text and adds it to a dictionary.

    Args:
        item: The item identifier.
        section: The section identifier.
        name: The key for the dictionary entry. see UITextsKeys.Msg
        ui_db_texts: UIDBTexts.
        args: Optional arguments for formatting the retrieved text.

    Returns:
        The formatted text.

    mgd 2025-10-30
    Check if texts contains the required item
    This will allow to set the items of sections [secSuccess, secError]
    in the 'current' section.

    """
    from ..common.app_context_vars import sidekick

    # take the default value for Item
    item = item or name
    # search in the messages dict
    msg_text: str = ui_db_texts.get_msg(item) if ui_db_texts else ""

    if not msg_text:
        # search in the items dict
        msg_text = ui_db_texts.get_str(item) if ui_db_texts else ""

    if len(ui_db_texts) == 0:
        # TODO: ui_db_texts can have no items, the next error message mask this situation. TODO:
        sidekick.display.warn(f"Warning: ui_db_texts[{ui_db_texts.section}] has no items.")

    if section and not msg_text:
        msg_text = db_retrieve_text(item, section)

    try:
        if is_str_none_or_empty(msg_text):
            value = ""
        elif not args:
            value = msg_text
        elif isinstance(args, dict):
            value = msg_text.format(**args)
        elif isinstance(args, tuple):
            value = msg_text.format(*args)
        else:  # simple
            value = msg_text.format(args)
    except Exception as e:
        sidekick.display.error(f"UIDBTexts, msg [{msg_text}] render error: [{e}].")
        value = msg_text

    if ui_db_texts and value:  # add or refresh
        ui_db_texts[name] = value

    return value


# Cached Texts retrievers ==================================
def get_section(section_name: str) -> DB_Texts:
    """
    returns a DBTexts of the 'section_name' from table vw_ui_texts
    """
    from ..common.app_context_vars import sidekick

    if is_str_none_or_empty(section_name):
        return {}

    table_cache = UITexts_TableSearch(ui_texts_locale(), section_name)

    if table_cache.exists():
        return table_cache.get_text()
    else:  # not in cache, retrieve section
        query = __get_ui_texts_query("item, text", table_cache)
        items = _get_query_as_dict(query) or {}
        # TODO: raise if section does not
        # if len(items) == 0:
        #     raise KeyError(f"UI texts section '{section_name}' for [{table_cache.locale}] not found or has no items.")
        items.update({UITextsKeys.Section.name: section_name})
        items.update({UITextsKeys.Form.date_format: table_cache.locale})
        items.update({UITextsKeys.Form.faStyle: sidekick.config.APP_UI_FONT_AWESOME_STYLE})

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

    db_texts = get_db_texts(ui_db_section)
    ## add to ui_db_texts useful values  of 'general use'
    ui_dt_format = sidekick.config.APP_UI_DATETIME_FORMAT
    db_lookup = cast(DB_Lookup, db_retrieve_text)
    ui_db_texts = UIDBTexts(db_texts, sidekick.debugging, ui_dt_format, db_lookup)

    return ui_db_texts


## ----- OBSOLETE  2026.04.02-----------
def set_msg_info(item: str, ui_db_texts: UIDBTexts, *args) -> str:
    """
    returns `text` for the [item, <curr_section>]
    and adds the pair to `texts` => texts.add(text, 'msgInfo')
    """
    return _set_or_add_msg(item, "", UITextsKeys.Msg.info, ui_db_texts, *args)


def set_msg_warn(item: str, ui_db_texts: UIDBTexts, *args) -> str:
    """
    returns text for the [item/'sec_Error'] pair
    and adds pair to texts => texts.add( text, 'msgError')
    """
    return _set_or_add_msg(item, UITextsKeys.Section.error, UITextsKeys.Msg.warn, ui_db_texts, *args)


def set_msg_error(item: str, ui_db_texts: UIDBTexts, *args) -> str:
    """
    returns text for the [item/'sec_Error'] pair
    and adds pair to texts => texts.add( text, 'msgError')
    """
    return _set_or_add_msg(item, UITextsKeys.Section.error, UITextsKeys.Msg.error, ui_db_texts, *args)


def set_msg_success(item: str, ui_db_texts: UIDBTexts, *args) -> str:
    """
    returns `text` for the [item, <curr_section>] | [item, 'sec_Success'] pair
    (of the vw_ui_texts view)
    and adds the pair to `texts` => texts.add(text, 'msgSuccess')

    Finally sets ui_db_texts.Msg.display_msg_only = True, so the form only displays
    the message (no other form inputs)
    """

    ui_db_texts.reset_messages()
    msg = _set_or_add_msg(item, UITextsKeys.Section.success, UITextsKeys.Msg.success, ui_db_texts, *args)
    ui_db_texts.display_msg_only = True
    return msg


def set_msg_fatal(item: str, ui_db_texts: UIDBTexts, *args) -> str:
    """
    Same as add_msg_error, but
    1) sets  ui_db_texts.display_msg_only = True,
       so the form only displays the message (no other form inputs)
    2) wipes all ui messages from the data dict
    """
    ui_db_texts.reset_messages()
    msg = set_msg_error(item or UITextsKeys.Msg.fatal, ui_db_texts, *args)
    ui_db_texts.display_msg_only = True
    return msg


# eof
