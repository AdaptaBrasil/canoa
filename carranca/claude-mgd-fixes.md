# Claude ↔ Miguel — Fix Log

Narrative record of bugs Claude found/fixed while reviewing Canoa source files with Miguel.
Kept separate from the source files themselves (no docstring stamps) and separate from
`mgd-logbook.txt` (Miguel's own dev diary — not for this).

Hot and short: an entry lives here until its fix is committed, then it leaves (the git history of
this file keeps it). The "Still open" list at the end holds what a fix left pending.
Each file's CRC32 at time of fix is tracked in `claude-certificate.txt`, the tamper-evidence ledger.

---
## 2026-11-12 22:00 — β 6.10 start-up log on the VM: clean, four cosmetic findings (not fixed)

Log `Canoa_2026-11-12_f87700.log`, first start after the deploy (`ce10f86`, new rema.sh, trimmed env file).
**Verified:** Production mode, `debug=False, reloader=off`, DB 5.14.0 on schema `canoa`, β 6.10, data_validate
0.7.65b732 found, log under `carranca/log_files/` with the start-up buffer in it, 29 info lines, 0 warnings, 0 errors.

Findings, in the log's own words:

```
sys|0:00.000[i]  Messages printed:  [i] 29, [▲] 0, [!] 0, , [🚨] 0
sys|0:00.000[i]  Started by `flask run` (debug=False, reloader=off).
sys|0:00.000[i]  Configured by environment variables: on the server, `.vscode/launch.json` in VS Code.
```

1. **Elapsed time back to `0:00.000`** on the last three lines. (`sys|` is the log file's user column, `sys` = no request,
   see `Sidekick._echo`; the console does not show it. Only the zeroed time is the finding.)
   Cause, `main.py:100` area: the summary block calls `set_elapsed_output(False)` then `set_elapsed_output(True)`;
   with no `elapsed_from` argument, `Display.set_elapsed_output` restarts the clock (`Display.py:252`), so every
   line after it counts from zero. Fix direction: keep the start time and pass it back, eg
   `was_active, t0 = ...` / `set_elapsed_output(True, elapsed_from=t0)`.
2. **Double comma** in the summary: `[!] 0, , [🚨] 0`. With debug off, `display.print(DEBUG, ...)` returns
   nothing (`or ""`), the loop still appends `", "`, and `strip(", ")` only trims the ends. Fix direction:
   collect the non-empty pieces in a list and `", ".join(...)`.
3. **`"app_mode": null`** in the args line although the mode came out as Production: the mode arrives via
   `CANOA_APP_MODE` a step after Args is printed. Same family as the DISPLAY_MUTE noise (memory
   `project_env_var_noise_display_mute`).
4. **Last line is wrong on the server**: "Configured by environment variables: on the server, `.vscode/launch.json`
   in VS Code." reads as if the server used launch.json; on the VM it is `rema.sh` + `canoa_env_vars.txt`.
   Fix direction: say "rema.sh on the server".

All four are in `main.py` / `Display.py`, one small step each, for the next batch (β 6.11).

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
