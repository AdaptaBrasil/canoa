# Claude ↔ Miguel — Fix Log

Narrative record of bugs Claude found/fixed while reviewing Canoa source files with Miguel.
Kept separate from the source files themselves (no docstring stamps) and separate from
`mgd-logbook.txt` (Miguel's own dev diary — not for this).

Hot and short: an entry lives here until its fix is committed, then it leaves (the git history of
this file keeps it). The "Still open" list at the end holds what a fix left pending.
Each file's CRC32 at time of fix is tracked in `claude-certificate.txt`, the tamper-evidence ledger.

---

(no entries: everything up to β 6.10 is committed, 76b03ed, 2026-11-12)

---

## Next jobs (agreed 2026-11-12)

a. **Grid generalization review**: `static/js/canoa_grid.js`, `tools/canoa_grid_test.js` and
   `docs/grid-generalization.md` (prototype of 2026-11-10, untracked, wired to no page). Review together,
   decide which of the four grid scripts (`sep_grid`, `sep_mgmt`, `scm_grid`, `spd_grid`) it replaces first.
b. **Revalidation process, full review + merge**: `validate_process/*` shared by upload and revalidation,
   the provisional `rv_*` files merged into the shared modules (`process(modules=)`), per the plan of
   2026-11-05 (`revalidate_file.py` mirrored on `receive_file.py`, section `revalidateFile`,
   `REVALIDATE_FILE = 1100`). Review first, merge second.

---
