# Canoa — Database Conventions

Compiled 2026-07-15 from `exported_data/Canoa DDL 2026-07-14.sql`, the model files under
`carranca/models/`, and the trigger `.sql` files kept alongside their Python callers. This is
Claude's read of patterns Miguel already uses — not a spec written up front — so treat it as a
first draft to correct/extend, not gospel.

---

## 1. Schema & object naming

- Everything lives under the `canoa` schema (`canoa.sep`, `canoa.log_user_sep`, ...).
- **Views**: `vw_` prefix — `vw_mgmt_seps_user`, `vw_schema_grid`, `vw_scm_sep`, `vw_log_user_sep`,
  `vw_user_data_files_count`.
- **Trigger functions**: `<table_or_view>__on_<event>()`, double underscore — `users__on_ins_upd()`,
  `vw_mgmt_seps_user__on_upd()`, `user_data_files__on_ins_upd()`. The trigger *name* itself
  sometimes drifts slightly from the function name it calls (e.g. trigger `vw_mgmt_users_sep__upd`
  → function `vw_mgmt_seps_user__on_upd()` — `users`/`seps_user` order differs). Known drift, not
  a rule to copy.
- **Constraints**: `<table>__<role>` — `log_user_sep__pk`, `log_user_sep__done_by_fk`,
  `log_user_sep__sep_fk`. Unique indexes seen as both `__udx` (`log_user_sep__batch_sep_oper__udx`)
  and `__uix` (`sep__sch_name_lower_uix`, per a `sep.py` comment) — pick one going forward, they've
  drifted.

## 2. Column patterns

- **Action pairs**: `<verb>_at` (timestamp) + `<verb>_by` (user id) — `done_at`/`done_by`,
  `ins_at`/`ins_by`, `edt_at`/`edt_by`, `ico_at`/`ico_by`, `del_at`/`del_by`.
- **Lettered pipeline timestamps**: `user_data_files` orders its process-step timestamps with a
  single-letter prefix so alphabetical order = chronological order in any DB tool's column list —
  `a_received_at, b_process_started_at, c_check_started_at, d_register_started_at,
  e_unzip_started_at, f_submit_started_at, g_report_ready_at, h_email_started_at`, ending in
  `z_process_end_at` — `z` reserved for the terminal timestamp regardless of how many steps get
  inserted in between later.
- **`_lower` mirror columns**: case-insensitive lookups/uniqueness get a paired lowercase column —
  `fullname_lower`, `name_lower`, `username_lower`, `ticket_lower`. In the ORM these are declared
  `Computed("")` (Python doesn't know/care about the actual SQL formula, just that the DB computes
  it — see `Sep.name_lower`).
- **`batch_code`**: `varchar(10)`, encodes `(days since 2024-11-01).(ms)`, both halves in base-22
  ("duovigesimal"). Used to group related log rows from the same logical operation
  (`log_user_sep.batch_code`, `sep.mgmt_batch_code`).

## 3. Trigger-managed columns are deliberately left unmapped in the ORM

When a column's value is set entirely by a DB trigger (not by application code), it's commonly
*not* declared in the SQLAlchemy model at all — with a comment explaining why and where to find
the value instead:
```python
# del_at, del_by: soft-delete columns, DB-trigger managed, not mapped here
# mgmt_users_at, mgmt_batch_code: DB-trigger managed (vw_mgmt_seps_user__on_upd),
#   exposed via MgmtSepsUser.assigned_at/batch_code instead
# error_handled, exit_code: DB-trigger/legacy managed columns, not mapped here
```
(`sep.py`, `user_data_files.py`). If you hit a column that "isn't in the model" while debugging,
check for one of these comments before assuming it's an oversight.

## 4. Updatable views use "pass-through" columns

Views with an `INSTEAD OF UPDATE` trigger (e.g. `vw_mgmt_seps_user`) expose extra columns that
don't correspond to any real underlying column — they exist purely so the app can write data
*into* the trigger via `NEW.<col>` on an `UPDATE ... SET` against the view. Read normally (a
`SELECT`), they just return a constant placeholder:
```sql
0 AS assigned_by,
' '::character varying(10) AS batch_code
```
The Python model marks these `# pass through column: 0` (see `MgmtSepsUser.assigned_by`) — don't
expect the SELECTed value to mean anything; only the write path matters.

## 5. Retiring things: mark obsolete, don't drop immediately

- Views: `COMMENT ON VIEW canoa.vw_mgmt_user_sep IS 'OBSOLETE';` — left in place (still queryable)
  rather than dropped, presumably for safety/rollback during a transition.
- Columns: `## obsolete  2026.04.02` comments in the model file, with an arrow to whatever replaced
  them (`upload_start_at ->`, `report_ready_ay -> g_report_ready_at`).
- The matching **repo-side** `.sql` copy of a confirmed-dead trigger function, on the other hand,
  *was* deleted outright this session (`vw_mgmt_user_sep__on_upd.sql`) — the DB object stays until
  Miguel decides to actually drop it, but there's no reason to keep a tracked copy of dead code.

## 6. User-facing errors raised from triggers

PL/pgSQL `raise exception` calls wrap the actual message in a sentinel so the Python layer can
extract just the human text and discard the Postgres noise:
```sql
raise exception '[^|ID do SEP não foi informado.|^]';
raise exception '[^|Não foi encontrado o registro do usuário "%".|^]', usr_new_name;
```
Pattern: `[^| ... |^]`, parsed on the Python side (see `try_get_mgd_msg` in `db_helper.py`).

## 7. Roles & grants

Every table/view consistently gets:
```sql
ALTER TABLE canoa.<obj> OWNER TO canoa_power;
GRANT ALL ON TABLE canoa.<obj> TO canoa_power;
GRANT SELECT[, UPDATE, INSERT] ON TABLE canoa.<obj> TO canoa_connstr;
```
Two roles: `canoa_power` (owner/admin) and `canoa_connstr` (the app's actual runtime connection).
`canoa_connstr` only ever gets the verbs the app needs — `SELECT` only for read-only
views/grids, `SELECT, UPDATE, INSERT` for writable tables/updatable views. **No `DELETE` grant
observed anywhere** — consistent with the soft-delete (`del_at`/`del_by`) pattern; rows get marked
deleted, never actually removed by the app role.

## 8. CRC32, not CRC16

Integrity/dedup checks (`sep.icon_crc`, `user_data_files.file_crc32`,
`received_files.file_crc32`) use `zlib.crc32`, stored as `BigInteger`/`int8` — CRC32's range
exceeds a signed `int4`, which was an actual bug fixed during the 2026-07 revision (columns were
originally `int4`).

## 9. Repo file organization mirrors the DB 1:1

- One Python file per table/view under `carranca/models/private/` or `carranca/models/public/`,
  named from the DB object (`vw_mgmt_seps_user` → `mgmt_seps_user.py` / `MgmtSepsUser`,
  `vw_schema_grid` → `schema_grid.py` / `SchemaGrid`).
- Trigger-function `.sql` bodies are kept near their Python "producer" module rather than
  centralized — e.g. `carranca/private/sep_mgmt/*.sql` next to `save_to_db.py`,
  `carranca/public/access_control/users__on_ins_upd.sql` next to the login/register code.
- `exported_data/` is a working folder for full-schema DDL dumps (tables/views/triggers/comments)
  — **note: these dumps do not include `CREATE FUNCTION` bodies**, only the `CREATE TRIGGER ...
  EXECUTE FUNCTION x()` wiring. The function bodies must be pulled separately (DBeaver → Functions
  node → generate DDL) and saved as their own `.sql` file if you want a repo backup.

---

## Known gaps as of 2026-07-15

- `user_data_files__on_ins_upd()`'s function body has no repo copy yet (only exists live in the
  DB) — see `project_next_tasks.md` "back up ALL trigger function bodies".
- `__udx` vs `__uix` for unique-index suffixes hasn't been reconciled.
- Trigger *name* vs trigger *function* name drift (`vw_mgmt_users_sep__upd` vs
  `vw_mgmt_seps_user__on_upd`) — cosmetic, not fixed.

---
<small>_eof_</small>
