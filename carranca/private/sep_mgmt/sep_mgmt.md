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
> carranca/private/seps_mgmt/
- `init_grid.py` *(main module)*
- `keys-values.py` *(front-end ↔ back-end keys/values, via class)*
- `save_to_db.py`
- `mgmt_notify.py`

### 📂 Jinja
> carranca/templates/private/
- `sep_mgmt.html.j2`

### 📂 Java Script
> carranca/static/js/
- `sep_mgmt.js`

### 📂 SQLAlchemy
> carranca/private/
- `models[MgmtUserSeps]`

---

## Database Objects

### 🏛 **Views**
- `vw_mgmt_seps_user`

### 🔄 **Triggers**
- `vw_mgmt_seps_user__upd` _(instead of update)_

### ⚙ **Functions**
- `vw_mgmt_seps_user__on_upd`

### 📊 **Table**
- `log_user_sep`

### 📊 **Columns**
- `sep.mgmt_sep_id`
- `sep.mgmt_sep_at`
- `sep.mgmt_batch_code`
