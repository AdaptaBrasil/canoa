# Claude ↔ Miguel — Fix Log

Narrative record of bugs Claude found/fixed while reviewing Canoa source files with Miguel.
Kept separate from the source files themselves (no docstring stamps) and separate from
`mgd-logbook.txt` (Miguel's own dev diary — not for this).

Hot and short: an entry lives here until its fix is committed, then it leaves (the git history of
this file keeps it). The "Still open" list at the end holds what a fix left pending.
Each file's CRC32 at time of fix is tracked in `claude-certificate.txt`, the tamper-evidence ledger.

---

## 2026-11-12 — sep_log_grid [Voltar] showed the raw `!@@` sentinel in the address bar

Open since 2026-07-21: [Voltar] posted straight to `/sep_grid/!@@`, so the `show` sentinel stayed visible after
the POST. **Fix:** the form now posts to `/sep_grid/form_cargo_id`, the route every sep_grid button already uses,
and the sentinel travels inside the hidden cargo input as the JSON sep_grid.js would send
(`{"act": "?", "code": "!@@", "idx": 0}`, action `unknown` = no action, code `show`): `_get_result()` in
routes.py accepts it and `grid_route()` sees `code == show` and redisplays the grid. From sep_mgmt the cargo
stays empty (its route redisplays on an empty cargo and would `json.loads` anything else). Plumbing:
`action_form__post_cargo` gained an optional `cargo=''` (value of the hidden input, HTML-escaped),
`UITextsKeys.Action.dlg_goto_cargo` (`dlgFormGotoCargo`) and `dlg_goto_cargo` in dialog.html.j2 carry it, set
by sep_log_grid.py next to `dlg_goto`. Verified with the route functions under a logged-in request context:
both origins render the log, and the POST back renders the SEP grid / the management grid with no error.

---
## 2026-11-12 — id obfuscation: the per-model seed was the numeric base, codes were digit-only

Found by Miguel: `/sep_log_grid/140?from=sep_mgmt` looked like a raw SEP id (it was `MgmtSepsUser.to_code(7)`).
Cause: `CanoaBase.__init_subclass__` passed `__code_seed__` (1..14 per model) as `IdToCode`'s first argument,
`instance_base`, so each model wrote its codes in base *seed*: base 9 for `MgmtSepsUser` (digits only, trailing
`0` from the `* base`), base 2 for `mgmt_email_sep` (binary strings), base 1 for `log_user_sep` (`to_base` raises
`ValueError`, never called so far). **Fix (IdToCode.py only):** fixed base 36, the seed is now the code's last
digit: `encode = to_base((id + 1000) * 36 + seed, 36)`, `decode` returns -1 unless `raw % 36 == seed`, then
`raw // 36 - 1000`. Codes carry letters (`rz9` for SEP 7 in `MgmtSepsUser`), no fixed trailing zero, and a code
made for one model is rejected by every other one instead of decoding to a random row. The constructor rejects
seeds outside `[1, 35]`. Callers (`to_code`/`to_id`, `ExportProcessConfig.coder`) unchanged; codes are computed per
page, nothing stored, old links are the only casualty (accepted). Round trip tested for all 14 seeds.

---
## 2026-11-12 — `request_loader` deleted (the passwordless fallback commented out on 2026-08-18)

Flask-Login's `request_loader` in `models/public/user.py` read `request.form["username"]` and returned that `User`
with no password check, so any POST carrying a `username` field authenticated that user for the request (seen
in register.py's welcome flow, 2026-08-18; present since 7780a62, 2025-05-14). It was commented out then, with
`TODO: remove in next version`. **Fix:** the block is gone, with the two imports only it used (`flask.Request`,
`is_str_none_or_empty`). `user_loader` is the only Flask-Login callback left.

---

## 2026-11-12 — the log folder followed the launch directory

Found by Miguel: an empty `log_files/Canoa_2026-08-13_*.log` at the repo root looked like a dead log. The
live files were in `carranca/log_files/`. `LOG_FILE_FOLDER` is a relative name and `do_log_file` joined it
with `.`, so the folder landed wherever the app was started from (repo root until August, `carranca/`
since). **Fix:** `BaseConfig.LOG_FILE_PATH = path.join(APP_PATH, LOG_FILE_FOLDER)` (same pattern as
`LOCAL_SPATIAL_DATA_PATH`), used by `do_log_file` and by `jinja_helper`'s rendered-template bugs file.
The stale root folder was deleted (ignored by git).

---

## 2026-11-12 — download errors showed Werkzeug's bare page instead of the styled one

Found by Miguel: the [Baixar] 404 of 2026-11-11 came out as the plain black-on-white Werkzeug page, with
the DB text's `&atilde;` escaped and the `(Error Code: 989, Logout: False, Fatal: True)` tail. Cause:
`abort_handler.py` set `g.raw_http_error_raised` and `_page_or_raw` (`__init__.py`) returned the raw error
on that flag. The flag came with f5e81a0 (2026-07-24): the handlers moved from `bp_public` to app-wide and
the download routes, until then uncovered by accident, were "kept as they were"; eba15fb (2026-08-13) then
documented it as "an HTML page would corrupt the binary download stream". That never held: `abort()` fires
inside the `except`, before `send_file()` builds a response, and the downloads are plain form POSTs
(`formtarget="_blank"`), so the browser renders whatever HTML the error status carries.
**Fix:** `abort_handler.py` raises `default_exceptions[code]` with the route's text attached as
`ui_tech_msg` (`e.msg (Error Code: N)` for an `AppStumbled`); `_error_page` (renamed from `_page_or_raw`)
shows the generic `HTTP-<code>` DB text and that detail in the technical box. Removed: the flag check,
`APP_RAW_HTTP_ERROR_RAISED` and the "see abort_handler for why" comments in the three download routes.
`spd_download.py` keeps a commented-out `_not_found(task_code + 8)` as a dated debug aid to reproduce the
server's missing-file 404.

---

## 2026-11-11 — [Baixar IDs] "string indices must be integers" and [Baixar] "noRecord" not found

Found by Miguel in the visual pass of the menus. (1) `get_id_values` (`spd_analysis.py`) assumed
`file_data['values']` is a list of row dicts (shape since b96f2cd, 2026-08-10). A record analyzed before
that has `{field: [unique values]}`; iterating the dict gives the key strings, and for the key equal to
`field_id` the test `field_id in row` is a substring test that passes, then `row[field_id]` raises.
**Fix:** a `dict` is read as the old shape (`rows.get(field_id, [])`), ids need no row pairing.
(2) `spd_download.py` asked for the UI text `noRecord`, which no section had: **fix** an insert in
`update_canoa.sql` (section `spdGrid`). (3) In `spd_download.py` and `sep_ids_download.py`, `_not_found(task_code)`
only used its parameter in the message; `_raise` read the enclosing `task_code`, so the page always showed
the same code whichever branch failed. **Fix:** `_not_found(branch_code)` sets the enclosing `task_code`
(`nonlocal`); `spd_download.py` also had two branches with `+5`, now `+5`, `+6`, `+7`. Not verified on the
server: the cause of the [Baixar] "no record" itself (DB record or the file on disk), the page now tells.

---
