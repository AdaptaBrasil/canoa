# UIDBTexts System — Architecture & Reference

> Covers the full pipeline from database `vw_ui_texts` to Jinja template variables,
> plus the icon system, dialog layout conventions, and the Ups! fatal-error path.
>
> Written after reading:
> `UIDBTexts.py`, `UITextsKeys.py`, `ui_db_texts_manager.py`,
> `display_html.py`, `ups_handler.py`, `dialog.html.j2`,
> `FormIcons.py`, `local_ui_texts.py`, `html_helper.py`
>
> mgd / Claude Sonnet 4.6 — 2026-06-26

---

## 1. Bird's-Eye View

```
DB view vw_ui_texts
  └─ get_section(section_name)          ← ui_db_texts_manager.py
       └─ UITexts_TableSearch (cache)
            └─ UIDBTexts(db_texts, ...)  ← common/UIDBTexts.py
                 └─ process_template(tmpl, **ui_db_texts.data())
                      └─ Jinja template (dialog.html.j2, etc.)
```

Every piece of visible text in the UI comes from the DB; there are **no hardcoded strings in templates**.
UI text lives in `db.vw_ui_texts`, grouped by `section` (= page/feature name) and keyed by `item`.

---

## 1b. Design Intent — Two Symmetric Patterns

The system has two consumers that follow the same pattern but from opposite sources:

| | `display_html.py` | `ups_handler.py` |
|---|---|---|
| **Purpose** | Render any named document (About, Privacy, Terms…) | Render a fatal-error dialog |
| **Text source** | DB via `init_ui_db_texts(section)` | DB via `get_section()` — with fallback |
| **Fallback** | Raises `AppStumbled` (error becomes an Ups! itself) | `local_ui_texts.py` (hardcoded) |
| **Template** | `home/document.html.j2` | `home/ups_page.html.j2` |
| **Both feed into** | `dialog.html.j2` | `dialog.html.j2` |

`display_html` is the **happy path**: it calls `**ui_db_texts.data()` and the template
receives everything — title, body, icon, style — as plain template variables, with no
per-document logic in Python.

`ups_handler` is the **failure path**: it cannot use the DB as its text source when the DB
is precisely what failed. `local_ui_texts.py` therefore carries hardcoded texts for all
three supported locales (`pt-br`, `en`, `es`). The locale is still known from the
Flask-Login session, which survives a DB outage — so the user still gets the error
message in their own language.

The icon pipeline (`formIcon` → `iconClass` → `iconSvgContent`) flows through both paths
unchanged, because icon keys are just more DB items — no special-casing per document type.

---

## 2. Key Files

| File | Role |
|---|---|
| `common/UITextsKeys.py` | Typed constants for all known item-key strings |
| `common/UIDBTexts.py` | Wrapper class — typed access over the raw `DB_Texts` dict |
| `helpers/ui_db_texts_manager.py` | Cache layer + DB queries + `init_ui_db_texts()` factory |
| `config/local_ui_texts.py` | Hard-coded fallback texts (DB-down scenario) |
| `config/FormIcons.py` | Font Awesome icon registry + `with_icon()` clone helper |
| `helpers/html_helper.py` | `icon_url()`, `icon_svg_inline()`, `img_filenames()` |
| `public/display_html.py` | Renders document dialogs (About, Privacy, Terms…) |
| `common/ups_handler.py` | Renders the fatal-error / "Ups!" dialog |
| `templates/layouts/dialog.html.j2` | Universal modal layout (all dialogs inherit this) |

---

## 3. `UITextsKeys` — Key Namespaces

```python
class UITextsKeys:
    class Msg:      # backend-msg.html.j2 targets
        ask     = "msgPrompt"  # rendered with no color, no icon
        error   = "msgError"
        fatal   = "msgFatal"
        info    = "msgInfo"
        success = "msgSuccess"
        tech    = "msgTech"
        warn    = "msgWarn"
        display_msg_only = "msgOnly"

    class Page:
        title = "pageTitle"

    class Form:     # dialog variables
        title     = "formTitle"
        icon_file = "iconFile"      # bare filename (e.g. "ups_handler.svg")
        icon_url  = "iconFileUrl"   # full URL (→ dlg_var_icon_url in template)
        btn_close = "closeFormButton"
        btn_submit = "submitFormButton"
        post_route = "formSubmitRoute"
        size      = "dlg_cls_size"

    class Fatal:    # ups_handler context
        no_db_conn = "NoDBConnection"
        code       = "UpsErrorCode"
        where      = "UpsOffendingDef"
        http_code  = "UpsHttpCode"

    class Section:
        error   = "secError"    # shared error messages
        success = "secSuccess"  # shared success messages
        current = ""            # search only in the loaded section
        name    = "__section_name__"  # internal: section name stored inside UIDBTexts
```

---

## 4. `UIDBTexts` — Internal Architecture

The constructor splits the incoming dict into **two internal dicts**:

```python
self._msg  = { k: v for k, v in data.items() if k in self.msg_keys }  # msgError, msgInfo, …
self._data = { k: v for k, v in data.items() if k not in self.msg_keys }
```

**Why two dicts?**  
Messages (`msgError`, etc.) can be overwritten during a request cycle without polluting the form-field data. `reset_messages()` wipes `_msg` keys from `_data`, keeping the data clean for the next render.

### Typed Accessors (all on `_data`)

| Method | Returns | Notes |
|---|---|---|
| `get_str(key, default="")` | `str` | Safe — returns default if missing |
| `get_bool(key, default=None)` | `bool` | Safe |
| `get_int(key)` | `int` | Raises on missing or None |
| `get_float(key)` | `float` | Raises on missing or None |
| `get_msg(key, default="")` | `str` | Reads from `_msg`, not `_data` |
| `set_value(key, value)` | `str` | Writes to `_data`; only `str | bool` accepted |
| `data()` | `Dict[str, Any]` | Returns a **copy** of `_data` with `display_msg_only` merged in from `_msg` — spread into `process_template()` |

### Message Helpers (class methods)

All return `(key_used: str, formatted_text: str)`.

| Method | Behaviour |
|---|---|
| `set_msg_prompt(key, args)` | Current section only (no DB fallback section), sets `msgPrompt`. Rendered with no color, no icon — see `backend-msg.html.j2` |
| `set_msg_error(key, args)` | Fetches from current section or `secError`, sets `msgError` |
| `set_msg_warn(key, args)` | Same, targets `secError` section, sets `msgWarn` |
| `set_msg_info(key, args)` | Fetches from current or `secSuccess`, sets `msgInfo` |
| `set_msg_success(key, args)` | Like info + `display_msg_only = True` |
| `set_msg_fatal(key, args)` | Like error + `display_msg_only = True` |

`display_msg_only = True` hides all form inputs in the template — only the message block renders.

### Text Lookup Priority (`_set_or_add_msg`)

1. `_msg` dict of the current section
2. `_data` dict of the current section
3. DB lookup in `alternative_section` (e.g. `secError`)
4. `_key_not_found_ui_msg()` — returns a visible "key not found" sentinel (self-reporting)

### Recursive Placeholder Resolution

`try_recursive(key, value)` resolves `{key_suffix}` placeholders in a text value by looking up
sibling keys in `_data`. Example: a text value `"Olá, {user_name}!"` containing `{user_name}`
would be filled from `self.get_str("user_name")`.

---

## 5. Cache Layer — `UITexts_TableSearch`

```
global_ui_texts_cache: dict[Cache_Key, DB_Texts | str]
Cache_Key = Tuple[section_lower, locale, item | None]
```

- **Section cache**: key `(section, locale, None)` → entire `DB_Texts` dict for that section.
- **Item cache**: key `(section, locale, item)` → single `str` value.
- Cache is populated on first access; never explicitly invalidated during a request.
- `get_section()` injects Jinja global strings and the section name into the cached dict.

`init_ui_db_texts(section)` is the factory used by route handlers:

```python
def init_ui_db_texts(section: str) -> UIDBTexts:
    db_texts = get_db_texts(section)       # hits cache or DB
    return UIDBTexts(db_texts, sidekick.debugging, ui_dt_format, db_lookup)
```

---

## 6. Icon Pipeline

### 6a. Font Awesome Icons (`FormIcons`)

`FormIcons` is a `FormIconsDict` (dict subclass with attribute access):

```python
fi = FormIcons          # global singleton
fi.fatal                # → "fa-bomb"
fi.with_icon("fatal")   # → clone of FormIcons with fi["icon"] = "fa-bomb"
```

In templates:
```jinja
{% elif fi and fi.icon %}
<i class="fas fa-fw dlg-fa-icon {{fi.icon}}" style="font-size:{{ dlg_icon_size }};"></i>
```

CSS color: `.dlg-fa-icon { color: var(--canoa-form-label-color); }`

### 6b. SVG File Icons — `<img>` path (legacy / non-CSS-color)

`UITextsKeys.Form.icon_url` (`"iconFileUrl"`) is set to a URL and passed as template variable.
`dialog.html.j2` renders it as `<img src="{{dlg_var_icon_url}}">`.  
**Limitation:** CSS `color` cannot propagate into an `<img>`-loaded SVG.

### 6c. SVG File Icons — Inline path (CSS-color-controllable)

`icon_svg_inline(svg_file_path)` in `html_helper.py`:
1. Reads the file.
2. Strips `<?xml …?>` (invalid inside HTML).
3. Adds `viewBox="0 0 W H"` if absent (derived from fixed `width`/`height`).
4. Replaces `width="N"` / `height="N"` with `width="100%"` / `height="100%"`.
5. Returns the raw SVG markup string, or `""` on error.

The result is stored as `"iconSvgContent"` in `ui_db_texts` / `ui_texts` and flows to the template.
`dialog.html.j2` renders it inside a sized `<span>` carrying the icon-class:

```jinja
{% if iconSvgContent %}
<span id="{{dlg_icon_id}}"
      class="dlg-icon-back-class {{dlg_var_icon_class | default('')}}"
      style="width:{{dlg_icon_size}};height:{{dlg_icon_size}};">
    {{ iconSvgContent | safe }}
</span>
```

CSS `color` on the `<span>` → SVG paths with `fill="currentColor"` → icon takes the theme color.

**Requirement:** SVG paths must use `fill="currentColor"` (not hardcoded hex).

### Priority order in `dialog.html.j2` header icon slot

```
1. iconSvgContent present  → inline SVG (CSS-color-controllable)
2. dlg_var_icon_url present → <img> (no CSS color)
3. fi.icon present          → Font Awesome <i> (CSS-color-controllable via .dlg-fa-icon)
```

---

## 7. `display_html.py` — Document Dialogs

Used for: About, Privacy, Terms of Use, and any section-keyed document in the DB.

**Icon resolution logic:**

```python
form_icon_key = "formIcon"           # DB key holding the icon filename
form_icon = ui_db_texts.get_str(form_icon_key)

if fi.get(form_icon):               # is it a known FA icon name?
    icon_key = form_icon            # → FA path
elif os.path.exists(..., form_icon): # is it a file on disk?
    set icon_url                    # → <img> fallback
    if form_icon.endswith(".svg"):
        set iconSvgContent          # → inline SVG (preferred)
```

Images referenced in `documentBody` are managed separately:
`img_filenames()` extracts them → `__prepare_img_files()` fetches missing ones from DB
→ `img_change_src_path()` rewrites `<img src>` paths in the body HTML.

---

## 8. `ups_handler.py` — Fatal Error Dialog

Entry points:
- `ups_handler(error_code, user_msg, e, logout)` → returns `(_, tmpl_file, ui_texts)`
- `get_ups_jHtml(ui_item_error_key, ui_db_texts, task_code, e)` → convenience wrapper

**Fallback chain when DB is unreachable:**
```python
try:
    ui_texts = get_section(f"Ups-{error_code}")  # section named "Ups-500" etc.
except:
    ui_texts = local_ui_texts(UITextsKeys.Fatal.no_db_conn)  # hardcoded in local_ui_texts.py
```

**Icon setup:**
```python
icon_file_name = ui_texts.get(UITextsKeys.Form.icon_file)  # "ups_handler.svg"
ui_texts[UITextsKeys.Form.icon_url] = icon_url(icon_file_name)  # URL path
# Also load inline for CSS-color control:
svg_path = os.path.join(current_app.static_folder, "icons", icon_file_name)
ui_texts["iconSvgContent"] = icon_svg_inline(svg_path)
```

CSS hook: `.dlg-ups-icon { color: var(--canoa-form-label-color); }`  
Set in `ups_page.html.j2` via `{% set dlg_var_icon_class= 'dlg-ups-icon' %}`.

---

## 9. `dialog.html.j2` — Variable Naming Convention

Variables set by child templates (before `{% extends %}`):

| Variable | Type | Source (child template) | Meaning |
|---|---|---|---|
| `dlg_var_v_centered` | bool | child | vertical-center the modal |
| `dlg_var_scroll` | bool | child | scrollable modal body |
| `dlg_var_icon_url` | str | child ← `iconFileUrl` | URL for `<img>` icon |
| `dlg_var_icon_class` | str | child ← `iconClass` | CSS class for icon span |
| `dlg_cls_size` | str | child | `modal-sm`, `modal-lg`, etc. |
| `dlg_cls_top` | str | child | Bootstrap margin-top class |

Variables read directly from the Python template context:

| Variable | Set by | Meaning |
|---|---|---|
| `iconSvgContent` | Python (`display_html`, `ups_handler`) | Inline SVG markup string |
| `iconClass` | DB via `ui_db_texts.data()` | CSS class name for the icon |
| `formTitle` | DB | Dialog header title |
| `fi` | Python | `FormIconsDict` for FA icon access |

Naming rule:
- `dlg_var_*` → Jinja variables set by the child template
- `dlg_cls_*` → CSS class strings
- `dlg_blc_*` → Jinja block names
- `dlg_id_*` or `*_id` → HTML element IDs
- `dlg_bke_*` → values sent from back-end (Python)

---

## 10. `local_ui_texts.py` — DB-Down Fallback

Provides hardcoded texts for the three supported locales (`pt-br`, `en`, `es`).
Loaded by `ups_handler` when `get_section()` raises. Also used by `local_form_texts()` to
populate default button labels and icon filenames that every dialog needs.

Structure:
```python
local_texts = {
    "pt-br": {
        "Form": {
            UITextsKeys.Form.icon_file: "ups_handler.svg",
            UITextsKeys.Form.btn_close: "Entendi",
            ...
        },
        UITextsKeys.Fatal.no_db_conn: { UITextsKeys.Msg.warn: "…" },
        ...
    },
    ...
}
```

---

## 11. Gotchas & Invariants

| # | Rule |
|---|---|
| 1 | **All UI text in DB** — never hardcode strings in templates. |
| 2 | **HTML entities for accented chars** in DB text only (e.g. `&atilde;`); Python code and comments use UTF-8. |
| 3 | `ui_db_texts.data()` returns a **copy** of `_data` (mutating it does not affect the instance) with `display_msg_only` merged in from `_msg` — every other `_msg` key stays excluded. Spread with `**` into `process_template()`. |
| 4 | `set_value()` / `__setitem__` accept only `str | bool`. Passing other types raises `TypeError`. |
| 5 | `display_msg_only = True` hides all form controls — set by `set_msg_success` and `set_msg_fatal`. |
| 6 | `reset_messages()` is called before `set_msg_success` / `set_msg_fatal` to avoid stale message mix. |
| 7 | `get_section()` returns a **copy** — callers cannot pollute the cache. |
| 8 | SVG icons must use `fill="currentColor"` on all paths to be CSS-color-controllable. |
| 9 | `icon_svg_inline()` returns `""` on any error — the template falls through to the `<img>` branch silently. |
| 10 | `img_local_path` is the absolute path for SVG reading; `os.path.join(*img_folders, …)` is the relative path used for `os.path.exists()` checks (CWD = APP root). |

---

<small>_eof_</small>
