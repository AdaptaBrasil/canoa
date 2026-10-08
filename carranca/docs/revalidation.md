# Revalidation — one SEP's stored file

Runs a file **already stored** through `data_validate` again (validator or SEP spatial data updated).
Refs #61, second layer of "Validar Visíveis" (`sep_validate.py`). 2026-09-16.

## Modules

| Module | Role |
|---|---|
| `private/revalidate_sep.py` | Entry point `revalidate_sep(udf_id)` → `(error_code, msg_id, msg_arg)`. Loads record, SEP & manager, builds `ProcessData`, lock, cleanup. No request/template. |
| `validate_process/rv_process.py` | Loop `rv_check → rv_register → unzip → spdata → submit → rv_email` + final DB update (mirrors `process.py`). |
| `validate_process/rv_check.py` | Infra checks (as `check.py`) + stored file exists, same size, same CRC32 (1 MiB chunks). |
| `validate_process/rv_register.py` | Hard link (copy fallback) of the stored zip under the new ticket, then **insert** a new record. |
| `validate_process/rv_email.py` | As `email.py`, with revalidation recipients (below). |

`unzip`, `spdata`, `submit` are reused unchanged.

## Key decisions

- **New record** per revalidation; `process_version = "rv2026.09.16"` marks it (the `rv` prefix).
- **Runs as `app_user`**, the user responsible for starting it (`id_users` column comment): his folders, lock & `id_users`,
  so the received files grid/download (`UserFolders(id_users)`) finds the linked zip & report.
  Only the stored file is read from the sender's folder (`UserFolders(udf.id_users)`).
- **Report recipients**: SEP manager → to manager, cc adm (`report_email_cc`). No manager → to adm, no cc.
  No manager & no adm cc → to `app_user`. Disabled manager: warning only.
- **SEP data is current**: `id_spd` = SEP's current `spd_id`.
- **Never happened → NULL**: `a_received_at`, `c_check_started_at`.
- **Size/CRC32 mismatch or missing file → abort before insert** (no record, log only), because `vw_export_data_files` takes the newest record per SEP regardless of `error_code`.
- **Hard link under the new ticket**: `stored_file_name = ticket_file_name` keeps downloads & export working.
- **Only the lock owner cleans up** (`lock_acquired`).

## Error codes

| Where | Base | Task codes |
|---|---|---|
| `revalidate_sep` | `SEP_VALIDATE` (1000) | 11 not power · 12 no record · 13 no SEP · 14 manager lookup · 15 process data · 16 lock folder · 17 locked/bad lock · 18 cleanup · 19 exception during process |
| `rv_check` | `RECEIVE_FILE_CHECK` (210) | as `check.py` + 14 missing file · 15 size · 16 crc32 · 18 exception |
| `rv_register` | `RECEIVE_FILE_REGISTER` (230) | 3 source = working file · 4 link/copy · 6 insert |

## Pending

1. **Wire it**: `sep_validate.py` POST → read selected `ExportGrid.id`, `js_form_sec_check()`, call `revalidate_sep`, show `msg_id`.
2. **Email text**: `rv_email.RV_EMAIL_TEXTS` still `uploadedFile_email`; needs DB section `revalidatedFile_email`.
3. **DB columns**: `id_source_udf`, `spd_crc32`, `spd_edited_at` (+ `db_version`).
4. **"All" SEPs**: needs a background job (request timeout).
5. **`receive_file.py` lock bugs** (found here, fix later): `_try_lock_process` returns `True` on `FileExistsError`; the `finally` cleanup runs even when the lock was *not* acquired (deletes a running process's lock & data folders).
6. **DRY**: merge `rv_process` into `process(modules=...)`; share lock/cleanup with `receive_file.py`; share infra checks with `check.py`; `rv_email` with `email.py`.

---
<small>_eof_</small>
