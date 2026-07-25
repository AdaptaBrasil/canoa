# `log_user_sep.operation` — Reference

> What each operation code actually means, where each one gets written, and two things that
> are easy to get wrong: `S` vs `R` are not symmetric, and `D` is reserved but unused.
>
> Written after reading:
> `database/DDL/Canoa_DDL.sql` (`log_user_sep` table, `vw_mgmt_seps_user__on_upd()` /
> `vw_mgmt_user_sep__on_upd()` triggers), `models/private/sep.py` (`Sep.save()`),
> `private/sep_log_grid.py`, plus a live query against `canoa.log_user_sep` /
> `canoa.vw_ui_texts` on 2026-07-24.
>
> mgd / Claude Sonnet 5 — 2026-07-24

---

## 1. The seven codes

The canonical definition is the column comment itself
(`Canoa_DDL.sql:375`):

```sql
COMMENT ON COLUMN canoa.log_user_sep.operation IS
  '(S)et, (R)emoved | (I)nserted (E)dited, marked as (D)eleted | schema (C)hanged,';
```

Two separate groups, by what they're about:

| Code | Meaning | About | Written by |
|---|---|---|---|
| `S` | Manager **Set** (assigned or replaced) | the SEP's manager | DB trigger `vw_mgmt_seps_user__on_upd()` |
| `R` | Manager **Removed**, none replacing them | the SEP's manager | same trigger |
| `I` | SEP **Inserted** | the SEP itself | `Sep.save()`, `models/private/sep.py:161` |
| `E` | SEP **Edited** | the SEP itself | `Sep.save()`, `models/private/sep.py:163` |
| `D` | (originally read as SEP marked **Deleted**) | — | **reserved, never written, and now deliberately left alone — see §3** |
| `C` | **Schema** changed (the SEP moved to a different Schema) | the SEP itself | `Sep.save()`, `models/private/sep.py:165` |
| `V` | Data submission **Validated** successfully | the SEP's data | `process.py` (added 2026-07-23) |
| `X` | SEP turned **eXportable** (`visible: False → True`) | the SEP's export eligibility | `Sep.save()`, `models/private/sep.py:166` (added 2026-07-24) |
| `F` | SEP turned **Forbidden** to export (`visible: True → False`) | the SEP's export eligibility | same, added 2026-07-24 |

Live counts as of 2026-07-24 (`SELECT operation, COUNT(*) ... GROUP BY operation`, before `X`/`F`
existed): `S`=55, `E`=123, `I`=17, `R`=2, `C`=3, `V`=1, `D`=0. Plus 49 rows with `operation IS
NULL` — see §4.

---

## 2. `S` vs `R` are NOT symmetric — read the trigger, not just the label

Both are written by the *same* trigger, `vw_mgmt_seps_user__on_upd()`
(`Canoa_DDL.sql:1327-1391`, an `instead of update` trigger on the `vw_mgmt_seps_user` view —
not Python, which is why grepping the codebase for these two codes finds nothing):

```sql
if NEW.user_new is Null or trim(NEW.user_new) = '' then
    if usr_curr_id is Null then
        return NEW; -- no-op: nobody was assigned anyway, don't log anything
    end if;
    operation := 'R';
    usr_new_id := Null;
else
    ... look up usr_new_id by username ...
    operation := 'S';
    -- (also a no-op / return NEW if usr_curr_id = usr_new_id: no real change)
end if;

insert into canoa.log_user_sep
    (id_users, id_sep, id_users_prior, done_at, done_by, batch_code, operation)
values (usr_new_id, NEW.id, usr_curr_id, done_at, NEW.assigned_by, NEW.batch_code, operation);
```

**The easy mistake**: assuming `R` means "this manager stopped managing the SEP" in general,
and that a manager *replacement* would also show up as `R` (for the outgoing manager) plus `S`
(for the incoming one). It doesn't. There is only ever **one** log row per assignment event:

- `NEW.user_new` **empty** → `'R'` — the SEP is left with **no** manager. `id_users` is set to
  `NULL`; `id_users_prior` records who was removed.
- `NEW.user_new` **non-empty** → `'S'` — covers *both* "first assignment" and "replaced the
  previous manager." `id_users_prior` still records who (if anyone) was replaced, but the
  operation code itself doesn't distinguish "first assignment" from "replacement" — both are
  `'S'`.

So: a straight manager-to-manager handoff (SEP X: Alice → Bob) is a **single `'S'` row**
(`id_users=Bob`, `id_users_prior=Alice`), never an `'R'` row for Alice. `'R'` only appears when
a SEP goes from *having* a manager to having *none*.

Validated against live data (2026-07-24): both existing `'R'` rows have `id_users IS NULL` and
a populated `id_users_prior` — consistent with the trigger logic above, no bug found.

---

## 3. `visible` isn't about UI visibility at all — and `D` stays retired

Originally assumed (from the column comment's wording, and from `D`'s `jsonOperation` label
`"Removido"`) that `sep.visible` controlled whether a SEP is hidden from the app, and that `D`
was the reserved-but-unwired code for that. Checked every actual usage of `.visible` in the
codebase (2026-07-24) and that assumption was wrong: `Sep.get_visible_seps_of_scm()`
(`models/private/sep.py:206`) is the **only** place `Sep.visible` is ever filtered on, and it's
called from exactly one place — `scm_data.py`'s `get_scm_data()`, which powers the Schema-export
screens (`scm_export_ui_display.py`, `scm_export_db.py`). Everywhere else — `/sep_grid`, the nav
menu, `receive_file.py`'s SEP picker, `sep_edit` itself — `visible` is completely inert. A
"hidden" SEP still shows up in its manager's menu, still accepts data submissions, still edits
normally (confirmed: `sep_form_data.py:69`'s `Sep.get_row()` and `sep_new_edit.py:212`'s
assignment have no visibility filter at all — restoring a hidden SEP back to `visible=True`
via the normal edit form already worked before this session, nothing needed fixing there).

**So the flag's real meaning is "is this SEP included when its Schema is exported," not "is this
SEP visible in the app."** The DB column comment on `canoa.sep.visible` was updated to say so
directly: `'When True the SEP will be exported (unrelated to UI display).'`

Given that, `D` (label `"Removido"`, sharing text with `R` but a different concept) was
deliberately **left retired rather than reused** — its original intent (from ~a year ago) isn't
fully certain, and building on an old guess seemed riskier than minting two fresh, clearly-named
codes for this specific, newly-understood feature:

- **`X`** — SEP turned eXportable (`visible: False → True`)
- **`F`** — SEP turned Forbidden to export (`visible: True → False`)

Implemented in `Sep.save()` (`models/private/sep.py:138,166-167`): a new `visible_changed: bool`
parameter, computed by the caller (`sep_new_edit.py:212-215`, same pattern as the existing
`schema_changed` bool — compare old vs new *before* mutating `sep_row.visible`, gated off
entirely for `SepEditMode.INSERT` since a brand-new row has no "old" value to compare against).
When true, logs `_log("X" if sep_row.visible else "F")` **in addition to** `"E"` — the same
precedent `schema_changed`/`"C"` already set in this function. That's a judgment call, not an
explicitly confirmed decision — could be revisited if a visibility-only save should skip `"E"`
entirely instead of logging both.

**Not yet done**: the `jsonOperation` DB text (`sepLogGrid` section) doesn't have `"X"`/`"F"`
label keys yet — until added, the log grid shows the raw letter for these two operations
instead of a proper label.

---

## 4. The 49 `NULL`-operation rows are pre-classification history, not a bug

`operation IS NULL` rows all date **2025-04-19 → 2025-06-24**; every classified row
(`S`/`R`/`I`/`E`/`C`/`V`) dates **2025-06-28 onward** — a clean cutover. The `operation` column
(and the whole S/R/I/E/D/C scheme) was added to the `vw_mgmt_seps_user__on_upd()` trigger on
**2025-06-28** (see the trigger's own inline comment: `-- mgd 2025-06-28 (S)et, (R)emoved |
(E)dited, Marked as (D)eleted.`). The 49 `NULL` rows simply predate the concept — they were
written back when `log_user_sep` already existed and tracked `id_sep`/`id_users`/`done_by`/
`batch_code`, just without any operation classification yet.

They're spread across 13 different `id_sep` values (as many as 14 for `id_sep=6`) with `done_by
= 2` (Miguel's own account) for 39 of the 49 — consistent with manual assign/reassign/remove
testing during early development, not a single bulk event. Reconstructing accurate `S`/`R`
values after the fact would require comparing each row's `id_users` against the *previous* row
for that same `id_sep` (`NULL → value` = `S`, `value → NULL` = `R`) — decided not worth doing
for pre-classification test data (2026-07-24).

---

<small>_eof_</small>
