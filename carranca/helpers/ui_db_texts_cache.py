"""
Equipe da Canoa -- 2024

texts_Helper.py
Retrieve ui texts item for current language
(refactored from helper.py)
mgd 2024-04-03

     🚧 work in progress


"""

# cSpell:ignore getDictResultset connstr adaptabrasil mgmt

from typing import TypeAlias, Optional, Tuple
from flask import current_app

from .py_helper import now
from ..common.UIDBTexts import UIDBTexts
from .ui_db_texts_helper import UITexts_TableSearch, ui_texts_locale

# === Global 'constants' form HTML ui ========================
cache_key: TypeAlias = Tuple[str, str, Optional[str]]


class UITexts_Cache:
    global global_ui_texts_cache
    _LAST_UPDATE_KEY = "last_update"
    _CACHE_INTERNAL_INFO_KEY: cache_key = (" ", "mgmt_data", "key")

    ## TODO SAVE is Cache _CACHE_INTERNAL_INFO_KEY
    _cfg_cache_lifetime_min = int(current_app.config.get("APP_UI_DB_TEXTS_CACHE_LIFETIME_MIN", 0))

    def __init__(self, section: str, item: Optional[str] = None):
        self.locale = ui_texts_locale().lower()
        # avoid a " " section (see CACHE_INTERNAL_INFO_KEY)
        self.section = section.strip().lower()
        self.item = item.lower() if item else None

    def _cache_item(self) -> bool:
        def _update() -> bool:
            self.set_info(self._LAST_UPDATE_KEY, now())
            return True

        def _cache_it() -> bool:
            _now = now()
            life_time = self.get_info_value().get(self._LAST_UPDATE_KEY, _now)
            elapsed_min = int((_now - life_time).total_seconds() / 60)
            if elapsed_min > self._cfg_cache_lifetime_min:
                global global_ui_texts_cache
                global_ui_texts_cache = {}
            return _update()

        # Match the cache lifetime configuration to determine the caching behavior
        match self.cache_lifetime_min:
            case 0:
                # No caching is enabled
                return False
            case -1:
                # Always cache
                return _update()
            case _:
                # True, but if cache is old, first reset cache then update
                # old = (elapsed time in min > _cache_lifetime_min)
                return _cache_it()

    def exists(self) -> bool:
        return self.as_tuple in global_ui_texts_cache

    def update(self, texts: UIDBTexts) -> None:
        if self._cache_item():
            global_ui_texts_cache[self.as_tuple] = texts

    def get_text(self) -> str | None:
        return global_ui_texts_cache[self.as_tuple] if self.exists() else None

    def set_info(self, key: str, info: any) -> None:
        cache_info = self.get_info_value()
        cache_info[key] = info
        global_ui_texts_cache[UITexts_TableSearch._CACHE_INTERNAL_INFO_KEY] = cache_info

    def get_info_value(self) -> dict:
        cache_value = global_ui_texts_cache.get(UITexts_TableSearch._CACHE_INTERNAL_INFO_KEY, {})
        return cache_value

    @property
    def as_tuple(self) -> cache_key:
        """Returns a tuple of all three attributes."""
        return (self.section, self.locale, self.item)


# eof
