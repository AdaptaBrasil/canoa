# Claude ↔ Miguel — Fix Log

Narrative record of bugs Claude found/fixed while reviewing Canoa source files with Miguel.
Kept separate from the source files themselves (no more docstring stamps — those were
clutter) and separate from `mgd-logbook.txt` (Miguel's own dev diary — not for this).

Each file's CRC32 at time of fix is still tracked in `claude-certificate.txt`, so that
ledger stays the tamper-evidence mechanism; this file is the human-readable "what and why."

---

## 2026-08-14 — `dialog.html.j2` footer row missing `align-items-center`

`<select>` in a dialog footer (`sep_validate`'s user-list dropdown) rendered visibly
misaligned against the neighboring buttons. `align-items-center` was on the outer
`dlg-modal-content-footer-id` div, but the actual flex row grouping the controls
(`dlg-btns-container-id`) only had `justify-content-center g-2` — missing its own
`align-items-center`. Moved the class down to the row that needs it; removed it from the
outer div since Bootstrap's `.modal-footer` already sets `align-items: center` by default,
so it was redundant there.

---

## 2026-07-24 — `SchemaData.coder` was dead weight, always `null` in every export

Last open item from the Refs #57 export-format review: `scm_data.py:36`'s
`self.coder = None  # coder` was never read or assigned anywhere else in the codebase
(confirmed via grep), always emitting `"coder": null` in every export's `metadata.json`.
Distinct from — and confusable with — `ExportProcessConfig.coder` (the real `IdToCode`
instance used to obfuscate PKs for the UI, actively used elsewhere). Neither Miguel nor
the code itself could account for its purpose, and `scm_import.py` (the export's
counterpart) doesn't reference it either. Removed. This closes #57.

---

## 2026-07-24 — `ExportProcessConfig.header`'s `"decoding"` claim didn't match reality

Flagged during Refs #57 export-format review (2026-07-23): `header.json` always claimed
`"decoding": "Base64 -> UTF-8"`, but `scm_export_db.py` constructs `ExportProcessConfig()`
with `encode_data` defaulting to `False`, so the export never actually Base64-encodes —
text fields ship as plain UTF-8. The literal in the `header` property ignored
`self.encode_data` entirely. Fixed by conditioning the value on the flag itself:
`"decoding": "Base64 -> UTF-8" if self.encode_data else "plain UTF-8, nothing to do"` —
single source of truth, no change needed anywhere else that reads `config.header`.

---

## 2026-07-21 — `grid.html.j2`'s `msgOnly` gating never actually worked, for any grid page

While wiring `sep_log_grid.py`'s `JumpOut` path (a graceful "not found"/"not allowed"
message instead of a crash — see the entry below), the message showed correctly, but a
leftover empty ag-grid ("No Rows To Show") also rendered below it, and the dialog title
showed the raw unformatted `"Log de {0}"` DB text instead of the SEP's name.

**Root cause, verified with a minimal Jinja reproduction (not guessed):** `grid.html.j2`
wrapped its block *declarations* — `dlg_blc_body`, `grid_blc_footer`, `grid_blc_javascript`,
`grid_blc_forms`, `base_blc_head_js` — inside one shared `{% if dlg_bke_display_ui %}`, so
that they'd only render when the page wasn't in `msgOnly` mode. Confirmed this is a genuine
Jinja limitation, not specific to this file: wrapping a `{% block %}` override in `{% if %}`
inside a child/middle template has **zero effect**, whether one block or several are
grouped, and whether or not the block calls `{{ super() }}` — Jinja registers a block
override unconditionally based on its presence in the child's source; the ancestor template
that actually *calls* `{% block x %}{% endblock %}` has no visibility into any conditional
that wrapped the override's *declaration*. Verified this precisely with `jinja2.Environment`
reproductions matching the real 3-level chain (`dialog.html.j2` → `grid.html.j2` →
`sep_log_grid.html.j2`) before touching the real file. This means `grid.html.j2`'s `msgOnly`
support has likely never worked correctly for *any* grid page (`sep_grid`, `scm_grid`,
`spd_grid` too) — just never previously exercised, since `sep_log_grid`'s `JumpOut` path was
the first early-exit case any of them hit.

**Fix:** moved the `{% if dlg_bke_display_ui %}` to live *inside* each block's own body
(between its `{% block %}`/`{% endblock %}` tags) instead of wrapping the declarations from
outside. Verified this pattern actually gates correctly, including at the real 3-level
nesting depth, and that a grandchild's undefined-variable reference inside a gated block
never even gets evaluated when the condition is false.

**Also fixed in the same pass, `sep_log_grid.py`:** the `Form.title` DB text
(`"Log de {0}"`) was only being formatted with the SEP's name *after* the
not-found/not-allowed check — so on the `JumpOut` path, it stayed raw and unformatted.
Moved the formatting up next to where `sep_fullname` is computed, before the check.
Confirmed `set_msg_fatal()`'s internal `reset_messages()` only clears `Msg`-namespaced
keys, not `Form.title`, so this reordering is safe.

---

## 2026-07-21 — `grid.html.j2` `msgOnly` gap, part 2: message text and close button were also missing

Follow-up to the entry above. After moving `{% if dlg_bke_display_ui %}` inside each
block's body, `sep_log_grid`'s `JumpOut` path correctly suppressed the empty ag-grid —
but the dialog body was then completely blank (no error text at all), and the footer had
no button whatsoever. Two more instances of the same root shape:

1. **Message text never rendered for any grid page.** `form.html.j2`'s `dlg_blc_body`
   block includes `includes/backend-msg.html.j2` directly and unconditionally (line 33) —
   that's the only place the `msgError`/`msgWarn`/etc. alerts actually get emitted.
   `grid.html.j2`'s own `dlg_blc_body` override never included it at all; the include had
   been placed instead inside `includes/grid-body.html.j2` (line 15), which is itself only
   reached when `dlg_bke_display_ui` is `True` — i.e. exactly the one case where a message
   isn't the point. So no page extending `grid.html.j2` (`sep_grid`, `scm_grid`, `spd_grid`,
   `sep_log_grid`) has ever shown its backend message text.
   **Fix:** moved the `{% include "includes/backend-msg.html.j2" %}` out of
   `grid-body.html.j2` and into `grid.html.j2`'s `dlg_blc_body` block, unconditionally,
   ahead of the `{% if dlg_bke_display_ui %}` grid include — matching `form.html.j2`'s shape.

2. **No footer button in `msgOnly` mode.** `grid.html.j2`'s `dlg_blc_footer_buttons` block
   only ever rendered `grid_blc_footer` (gated by `dlg_bke_display_ui`) — the page-specific
   footer (e.g. `sep_log_grid.html.j2`'s only button, "Voltar") lives entirely inside that
   gated block, so in `msgOnly` mode there was no way to close the dialog at all.
   **Fix:** added an `{% else %}` branch to `dlg_blc_footer_buttons`, rendering a generic
   close button via `btn_close_dlg(dlg_close_form_id, dlg_close_btn_id, ...)` against the
   base close-form already defined unconditionally in `dialog.html.j2`'s `base_blc_forms` —
   same pattern `form.html.j2` uses for its own message-only footer.

Both verified live by Miguel against `sep_log_grid`'s not-allowed message (screenshot: alert
text + OK button both render correctly now).

**Still open, not yet applied (continue next session):**
- The dialog title still shows the raw `"Log de {0}"` placeholder on this same screen, even
  though the message body's own `sep_fullname` substitution works fine — so `sep_fullname`
  itself is a valid non-empty string, but `ui_db_texts.format(UITextsKeys.Form.title, ...)`
  isn't landing. Not yet traced further.
- The "Voltar" button posts straight to `/sep_grid/!@@` — functionally correct (`grid_route`
  in `routes.py` decodes the `!@@` "show" sentinel fine, same pattern used by
  `sep_new_edit.py`/`scm_new_edit.py`/`spd_new_edit.py`), but the raw sentinel is visible in
  the browser's address bar after the POST, since `action_form__post_cargo`'s `action`
  attribute is the URL directly. Proposed scoped fix (agreed in shape, not yet applied):
  route the POST through the existing `JS_FORM_CARGO_ID` cargo mechanism instead — target
  the form at `private_route("sep_grid", code=JS_FORM_CARGO_ID)`, add an optional
  `cargo=''` param to `action_form__post_cargo` (`_action_forms_and_btns.html.j2`) that sets
  the hidden cargo input's `value`, and pass `dlg_post_sec_msg` as that cargo value from
  `sep_log_grid.html.j2` (it already equals `UiActResponseProxy.show`). This makes the
  visible POST target `/sep_grid/form_cargo_id` instead of `/sep_grid/!@@`, same security
  check on the way back in. Deliberately scoped to this file + the one shared macro, not the
  broader `dlg_goto_action_url`/`prompt_back_route` standardization already on the
  next-tasks list.

---

## 2026-07-18 — crossed `extra` param in `action_form__post_cargo`, plus `UITextsKeys.Action` adoption

While building the security-token `extra` context-binding, `prompt.html.j2:77` ended up passing
`dlg_post_sec_msg` into `action_form__post_cargo`'s existing 4th positional param — which is
called `extra` too, but is actually raw HTML attributes dumped into the `<form ...>` tag (used
for real by `sep_mgmt.html.j2`'s `onsubmit=...` and `received_files_mgmt.html.j2`'s
`target="_blank"`). Same name, two different meanings — the macro's own hidden security input
never received the value at all. No live bug (nothing sets `dlgPostSecExtra` from Python yet, so
it was always `''`), but the wiring didn't do what it was meant to. Fixed by giving the macro a
separate `sec_extra=''` parameter (`_action_forms_and_btns.html.j2`), used in its
`safe_token.value(sec_extra)` call, and updating `prompt.html.j2` to pass it as an explicit
keyword arg (`sec_extra=dlg_post_sec_msg`) instead of colliding positionally with `extra`.

Also replaced the three remaining raw string literals (`"dlgFormCloseAction"`) with
`UITextsKeys.Action.dlg_close` in `sep_new_edit.py`, `scm_new_edit.py`, `spd_new_edit.py` —
`sep_log_grid.py` already used the constant form; these three were the last holdouts.

---

## 2026-07-18 — sep_log_grid: blank names, garbled header, raw datetime string

Three independent bugs found from one screenshot of the working grid:

1. **Blank "Gestor"/"Gestor anterior" columns.** Traced to the raw DB, not the view or
   template — `log_user_sep.id_users`/`id_users_prior` were genuinely `NULL` for the I/E
   rows shown. `Sep.save()`'s `_log()` closure (`models/private/sep.py`) only ever set
   `id_sep`/`done_by`/`operation`/`batch_code` — `id_users` is only ever populated by the
   DB trigger, for S/R (assign/remove) operations. Fixed: `_log()` now also sets
   `log_row.id_users = sep_row.users_id` (the SEP's current manager at that moment), so
   Insert/Edit/schema-Change entries show who was managing the SEP when they happened.
   Note: this only fixes new writes going forward — the two already-logged rows for this
   SEP stay `NULL` unless backfilled (not done, not asked for).

2. **`Operação` header showed literally as `Opera&ccedil;&atilde;o`.** `ui_items.text` is
   normally ASCII-with-named-entities (`carranca/tools/encode-for-ui_items-table.py`), but
   Miguel checked the DB across every grid section and found `colMetaInfo` is a deliberate
   **exception** to that rule: it's consumed as plain JS text (`ag-grid` `headerName`/cell
   values via `js_ui_dictionary()`), which doesn't HTML-decode, so raw UTF-8 is the correct
   form there — confirmed by `sepGrid`/`scmGrid`/`sepMgmt`/`spdGrid` all storing it that
   way already. `sepLogGrid`'s `operation` entry using entities was the actual outlier.
   Fixed defensively (not by touching DB text) in `static/js/sep_log_grid.js`: a small
   `decodeHtmlEntities()` (scratch `<textarea>`, read back `.value`) applied to every
   column's `headerName`, so it renders correctly whether the underlying text is raw UTF-8
   (the norm) or entity-encoded (harmless no-op). Took a couple of wrong turns getting
   here — first assumed it was a DB bug, then genuinely wasn't sure if the JS decode step
   was even necessary until Miguel tested it directly — worth double-checking assumptions
   like this against real DB content instead of guessing from one screenshot next time.

3. **`done_at` showed the raw string `Wed, 19 Nov 2025 09:56:2...`.** Flask's default
   JSON provider serializes `datetime` via `http_date()` (RFC 1123), and that's exactly
   what `{{ log_data | tojson }}` was sending straight to the grid. Fixed server-side in
   `sep_log_grid.py`, formatting each row's `done_at` with the existing (previously
   zero-caller) `helpers/py_helper.py:datetime_for_ui()` — `"%d/%m/%Y às %H:%M"`.

---

## 2026-07-18 — `sep_log_grid.html.j2` missing its ag-grid init script

Every other grid page (`sep_grid`, `scm_grid`, `spd_grid`) pairs its `.html.j2` with a
`static/js/<name>_grid.js` file that actually calls `agGrid.createGrid(...)`.
`sep_log_grid.html.j2` set up the `colMeta`/`gridRows`/`gridID` JS constants but never
called `createGrid` — the dialog would have opened with a permanently empty grid body.
Confirmed via DB (`ui_items.colMetaInfo`/`jsonOperation` for `sepLogGrid`, and
`vw_log_user_sep`'s columns) that everything else feeding the template was already
correct and in place; only the JS file itself was missing.

Added `carranca/static/js/sep_log_grid.js` — a read-only variant of the `scm_grid.js`
pattern (no `cargo`/action-form wiring, since this grid has nothing to submit): builds
`columnDefs` generically from `colMeta` with a small per-field `flex` map. Wired it in
via `<script src="{{static_route('js/sep_log_grid.js')}}"></script>` in
`sep_log_grid.html.j2`.

---

## 2026-07-18 — `carranca/private/received_files/init_grid.py`

Stale `.user_id` references on `ReceivedFilesCount` rows (lines 40, 45, 54), orphaned by
the 2026-07-15 `vw_user_data_files_count` column rename (`user_id → id`, see below). Every
other caller of that model got updated in that commit; this one was missed. Threw
`AttributeError: 'DBRecord' object has no attribute 'user_id'` whenever a power user opened
Received Files management — caught by the route's `except`, so it degraded to an "Ups!"
error screen rather than crashing outright. Confirmed via `Canoa_2026-07-18_8ie342.log`.
Fixed: `.user_id` → `.id` in all three spots. Confirmed no template/static JS depends on
the old attribute name.

---

## 2026-07-16 — batch review of `carranca/common/`

- **`Args.py`** — `ignite()`'s `cls(**data)` didn't match `__init__`'s signature; would
  raise `TypeError` if ever called. Now builds via `cls(app_debug)` + `__dict__.update()`.
- **`Display.py`** — `code()` built a `ValueError` but never raised it, and its range
  missed the bright codes 90/91 that `default` itself uses. Fixed both.
- **`app_context_vars.py`** — `if app_user is None:` was dead code (a `LocalProxy` is
  never `is None`); changed to `if not app_user:`. (Double-conversion in
  `__prepare_user_seps` still open — tracked in memory, not this file.)
- **`UIDBTexts.py`** — `get_bool()` could return `None` despite its `-> bool` annotation;
  default is now `False`. Deleted `_get_ui_datetime()`, dead code duplicating
  `get_ui_datetime()`'s first line.
- **`UITextsKeys.py`** — reviewed, no errors found.
- **`app_error_assistant.py`** — `proper_user_exception()` accessed `app_user.id` before
  the `if app_user` guard; crashed with `AttributeError` when called with no logged-in
  user. Guarded it like the next line already does. (`RECEIVE_FILE_EXCEPTION = 100`
  looks like it aliases `ACCESS_CONTROL_LOGIN`, but README.md documents "+100" as the
  deliberate exception offset — left as-is, not a bug.)
- **`igniter.py`** — `_get_debug_2()` did `bool(get_envvar(...))`; `bool()` of any
  non-empty string is always `True`, so debug was unconditionally on regardless of
  `CANOA_DEBUG`. Switched to the existing `as_bool()` helper.
- **`app_constants.py`** — reviewed, no errors found.

---

## 2026-07-15 — `carranca/common/Sidekick.py`

`_echo`'s `match` was missing the `FATAL` (and any future unhandled `Kind`) case, so
fatal-level messages were printed to console but never reached the log file or DB. Added
the missing case.
