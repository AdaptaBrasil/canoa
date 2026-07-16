# SEP Management and User Assignment

> **Note:** SEP is an old acronym for
> _"Strategic Planning Sector"_ (_Setor Estratégico de Planejamento_),
> retained until we find a better name.

## Equipe da Canoa -- 2024

| Date Range            | Version | Description           |
|-----------------------|---------|-----------------------|
| 2024-10-09 – 2025-04-09 | v1.0   | One user ↔ One SEP   |
| 2025-04-03            | v2.0   | One user → Several SEPs|
| 2025-04-09 – 2025-05-14 | Refactor | System refactoring |
|


## Files involved

### 📂 Python
> carranca/private/sep_mgmt/
- `sep_mgmt.py` *(main module)*
- `keys_values.py` *(front-end ↔ back-end keys/values, via class)*
- `save_to_db.py`
- `sep_mgmt_notify.py`

### 📂 Jinja
> carranca/templates/private/
- `sep_mgmt.html.j2`

### 📂 Java Script
> carranca/static/js/
- `sep_mgmt.js`

### 📂 SQLAlchemy
> carranca/models/private/
- `MgmtSepsUser` (`mgmt_seps_user.py`)
- `LogUserSep` (`log_user_sep.py`)
- `LogUserSepGrid` (`log_user_sep_grid.py`) — read-only audit-log grid, 2026-07-15

---

## Database Objects

### 🏛 **Views**
- `vw_mgmt_seps_user`
- `vw_log_user_sep` — read-only, added 2026-07-15 to support the (still unbuilt) admin UI for the "Registrar (logar) a criação e remoção de setores estratégicos" issue

### 🔄 **Triggers**
- `vw_mgmt_seps_user__upd` _(instead of update)_

### ⚙ **Functions**
- `vw_mgmt_seps_user__on_upd`

### 📊 **Table**
- `log_user_sep`

### 📊 **Columns**
- `sep.mgmt_users_id`
- `sep.mgmt_users_at`
- `sep.mgmt_batch_code`

---

## Obsolete (removed 2026-07-15)

`vw_mgmt_user_sep` / `vw_mgmt_user_sep__on_upd` — the v1.0 "one user ↔ one SEP" trigger (`users.mgmt_sep_id`-based). Already marked `COMMENT ON VIEW ... IS 'OBSOLETE'` in the DB; the matching `.sql` file in this folder was deleted from the repo since it referenced columns (`log_user_sep.id_sep_old`/`sep_new`) that no longer exist in the current schema.
