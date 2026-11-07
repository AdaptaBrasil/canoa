**Index**

- [Canoa Screen Commands](#canoa-screen-commands)
  - [Start Canoa (in a screen session)](#start-canoa-in-a-screen-session)
  - [Detach from screen](#detach-from-screen-leave-it-running-stay-detached)
  - [List screen sessions](#list-screen-sessions)
  - [Reattach to an existing screen session](#reattach-to-an-existing-screen-session)
  - [Stop Canoa (keep the screen)](#stop-canoa-keep-the-screen)
  - [Kill a screen session](#kill-a-screen-session)
  - [Last resort: kill a stuck Canoa process](#last-resort-kill-a-stuck-canoa-process)
- [Power of Linux](#power-of-linux)
  - [Working over SSH, current shell session](#working-over-ssh-current-shell-session)
  - [Power off immediately](#power-off-immediately)
- [Debug Mode](#debug-mode)
  - [How `APP_DEBUGGING` is resolved at startup](#how-app_debugging-is-resolved-at-startup)
  - [Turning it on locally](#turning-it-on-locally)
  - [Start-up log: verbose by default](#start-up-log-verbose-by-default)
  - [Active DB badge (navbar brand and dialog title)](#active-db-badge-navbar-brand-and-dialog-title)
  - [What flips when debugging is on](#what-flips-when-debugging-is-on)
  - [`debug_info.py`: captured but not yet shown anywhere](#debug_infopy--captured-but-not-yet-shown-anywhere)

---

# Canoa Screen Commands

```screen``` refers to the Linux command-line tool GNU Screen, a terminal multiplexer.

It allows you to:
   - Start a command (like flask run)
   - Detach from it and close your SSH/RDP session
   - Reattach later and continue exactly where you left off
   - -Keep long-running processes alive even if your connection drops

GNU Screen is not a windowing system nor physical terminal. It is a software tool that creates “virtual terminals” inside your real terminal.

## Start Canoa (in a screen session)

1. Check whether a Canoa screen exists. It can exist with Canoa stopped: a screen is only a
   shell, and `Ctrl + C` stops `flask run` but leaves the screen open.
   ```
   screen -ls
   ```
   Check whether Canoa itself is running (a printed line means running):
   ```
   ss -ltnp | grep 5001
   ```
2. If a screen exists, choose one:
   - **Canoa stopped, screen idle:** use it and go to step 4. If you are already inside it
     (`echo $STY` prints `1887.canoa`) you don't need `screen -dr`, it refuses with
     "Attaching from inside of screen?".
   - **Canoa running:** stop it first (see "Stop Canoa" below), then use the screen as above.
   - **Kill the whole screen** (hard, no `Ctrl + C`; replace `12345` with the actual session id),
     then start a new one in step 3:
     ```
     screen -X -S 12345 quit
     ```
3. Start a new screen session:
   ```
   screen -S canoa
   ```
4. Inside the screen session, go to the app dir and launch it -- no need to activate
   the venv yourself, `rema.sh` does it (`source ../.venv/bin/activate`):
   ```
   cd /home/desenv/canoa/carranca
   ../rema.sh
   ```
5. Detach, leaving it running: `Ctrl + A` then `D`

## Detach from screen (leave it running: stay detached)
Press: Ctrl + A then D

## List screen sessions
```
screen -ls
```

## Reattach to an existing screen session
Use `-dr` (detach elsewhere, then reattach here). It also works when `screen -ls` shows
`(Attached)`, which is what an SSH session closed without detaching leaves behind;
plain `screen -r canoa` fails then with "There is no screen to be resumed".
```
screen -dr canoa
```
If the name does not match, use the full id from `screen -ls`:
```
screen -dr 123456.canoa
```

## Stop Canoa (keep the screen)
Run `echo $STY` to see where you are, then pick the row that matches:

| `echo $STY` prints | You are | Do this |
|---|---|---|
| `1887.canoa` | inside Canoa's screen | `Ctrl + C`, then `Ctrl + A` `D` |
| another name | inside another screen | `Ctrl + A` `D` first, then the steps below |
| nothing | in a normal shell | the steps below |

`screen` refuses to attach from inside a screen ("Attaching from inside of screen?"),
that is why the first two rows skip `screen -dr`.

Steps (normal shell):
1. `screen -dr canoa`
2. `Ctrl + C` stops `flask run`, leaving the shell prompt inside the screen
3. `Ctrl + A` then `D` detaches (or type `exit` to close the screen too)

From anywhere, without attaching: `screen -S canoa -X stuff $'\003'` (sends Ctrl + C to the
`canoa` screen).

Check: `ss -ltnp | grep 5001` prints nothing when Canoa is stopped.

## Kill a screen session
Outside screen:
```
screen -S canoa -X quit
```

Inside screen:
Press: Ctrl + A then K, confirm with y

## Last resort: kill a stuck Canoa process
Only when `Ctrl + C` does not work (see also screen-guide.md, "Screen Detached from Terminal").
Try `kill <PID>` first, `kill -9` only if it survives.
```
ps aux | grep flask
kill <PID>
```

# Power of Linux

## Working over SSH, current shell session:
```
    exit
    `or Ctrl + D
```
## Power off immediately
```
logout && sudo shutdown -h now
```

---

# Debug Mode

Canoa has no single `DEBUG` switch. Startup resolves one `config.APP_DEBUGGING` flag, then
a handful of independent sub-flags derive from it. `sidekick.debugging` is just a copy of
`config.APP_DEBUGGING`, kept on the hub every request-scoped module already imports.

## How `APP_DEBUGGING` is resolved at startup

`igniter.ignite_app()` runs this chain once, before the Flask app exists:

Priority: 1. `--app_debug` argument, 2. env `CANOA_DEBUG`, 3. the mode's own `APP_DEBUG`.

1. `_get_debug_2()` ([igniter.py](../common/igniter.py)) reads the `CANOA_DEBUG` env var
   (`get_envvar("debug", ...)` prefixes it with `CANOA_`) via `as_bool()`. It returns `None`
   when the variable is unset: no config has been selected yet, so the mode's default is
   applied later (step 4).
2. `Args(debug_2).from_arguments()` ([Args.py](../common/Args.py)) seeds `app_debug` from
   that value, then `set_flags_from_argv()` lets a `--app_debug` command-line flag
   force it `True` (any attribute of `Args` can be forced `True` this way by name).
3. `Fuse.debugging = args.app_debug` (`True`, `False` or `None` = not informed).
4. The app mode (`Development` / `Stage` / `Production`) picks a config class. In
   `DynamicConfig.__init__()` ([DynamicConfig.py](../config/DynamicConfig.py)):
   `APP_DEBUG` = the mode's default (`True` for `DevelopmentConfig`/`StageConfig`, `False`
   for `ProductionConfig`) **unless `fuse.debugging` is not `None`**, which overrides it in
   both directions (`CANOA_DEBUG=False` turns debug off in Development).
   This happens before the sub-flags are propagated (next section), so they stay consistent.
   Then `_ignite_config()` sets `config.APP_DEBUGGING = config.APP_DEBUG`.
5. `Sidekick.debugging = bool(config.APP_DEBUGGING)` ([Sidekick.py](../common/Sidekick.py))
   is what the rest of the app actually reads at runtime.

⚠️ `igniter.py` repeats the warning inline: **don't run with debug turned on in production.**

## Turning it on locally

- VS Code: [launch.json](../../.vscode/launch.json)'s "Canoa" config already sets
  `CANOA_DEBUG=true` and `FLASK_DEBUG=1` as env vars for the debug session. That config sets
  no `CANOA_APP_MODE`, so it runs `Development`; with `CANOA_DEBUG=False` debug is really off.
- Shell: `export CANOA_DEBUG="True"` before `../rema.sh` (see
  [canoa_env_vars.txt](../../canoa_env_vars.txt)). `FLASK_DEBUG` is Flask's own reloader/
  debugger switch and is independent from `CANOA_DEBUG` — Canoa's flag drives
  `config.APP_DEBUGGING`, not Flask's.
- CLI: pass `--app_debug` as an argument to `main.py`.

## Start-up log: verbose by default

The start-up log (info, warn and error lines of every `igniter` step) is shown in **every**
mode, Production included. The debug-kind lines (`[¤]`) show only when debugging:
`Args.display_debug` follows `CANOA_DEBUG` and, once `create_app()` finishes, `display.debug_output`
is set to the final `APP_DEBUGGING` (which includes the mode's own default).

To silence the start-up log (everything, errors included):
- env `CANOA_DISPLAY_MUTE="True"` (e.g. in `canoa_env_vars.txt`). This is the way on the server:
  `flask run` rejects unknown arguments, so `--display_mute` does not reach Canoa there.
- argument `--display_mute`, when Canoa is started some other way (e.g. `main.py`).

Windows note: when the output is piped (`... | head`), set `PYTHONIOENCODING=utf-8`,
or the `β` of the app version raises `UnicodeEncodeError` (cp1252).

## Active DB badge (navbar brand and dialog title)

**Badge** = the navbar brand (and the `[name]` in the dialog title) that shows which database
the app is really talking to. Both values are computed once in `create_app()`
([\_\_init\_\_.py](../__init__.py)); the template variables are `app_brand` and `app_brand_alert`
(the Python name of the latter is `app_mismatch_schema`):

- `db_schema` comes from `current_schema()` right after the first connection
  ([igniter.py](../common/igniter.py), `_ignite_sql_connection`), so it is the schema the
  server *really* resolved from `search_path`, not a configured name.
- `app_brand` = app name on the production schema (`APP_SCHEMA = "canoa"`, see
  [app_constants.py](../common/app_constants.py)), otherwise the schema itself (e.g. `canoa_dev`).
- `app_mismatch_schema` = `(APP_MODE is Production) != (schema is production)`, shown red
  (`.brand-alert`). **Debugging is not part of it.**

| App mode (`APP_MODE`) | Schema    | Badge             | Meaning                                |
|-----------------------|-----------|-------------------|----------------------------------------|
| Production            | canoa     | Canoa             | expected                               |
| Production            | canoa_dev | canoa_dev (red)   | alert: running on the development DB   |
| Development, Stage    | canoa_dev | canoa_dev         | expected                               |
| Development, Stage    | canoa     | Canoa (red)       | alert: running on the live data DB     |

The same table lives in the header of
[navigator.html.j2](../templates/includes/navigator.html.j2).

**Console and log file.** A browser is not the only place to notice it, `create_app()` also logs:
- `[!] Canoa is in <mode> mode using the production DB [canoa].` or
  `[!] Canoa is in <mode> mode using a develop DB [canoa_dev].` whenever the badge is red;
- `[▲] Debugging is ON on the production DB.` when debugging is on and the schema is
  production, whatever the mode (the badge is red only if the mode is not Production too).

**To check/fix a mismatch:**
- `CANOA_SQLALCHEMY_DATABASE_URI` changes the current schema (its `search_path`);
- `CANOA_APP_MODE` changes the application mode.

**Red is a symptom, not a badge bug.** The app mode and the schema do not fit. Usual causes:

1. **App mode did not select the config** (found 2026-11-06, fixed 2026-11-07). `rema.sh`
   exports `CANOA_APP_MODE="Production"`, but `Fuse` ([igniter.py](../common/igniter.py))
   only read `args.app_mode`, which is always `None`, so it defaulted to `Development` and
   `DevelopmentConfig` (`APP_DEBUG=True`) was built. The env loop in
   [DynamicConfig.py](../config/DynamicConfig.py) then only overwrote the `APP_MODE` label
   on that instance, so the log claimed "Production".
   Now `Fuse` resolves the mode by priority: 1. `Args.app_mode`, 2. env `CANOA_APP_MODE`,
   3. `Development` when debugging (`CANOA_DEBUG` / `--app_debug`), otherwise `Production`
   (a missing mode fails safe). An unknown value (e.g. `production`, the match is case-sensitive)
   stops the startup with "Unknown app_mode".
2. **The DB URI points to the wrong schema.** The schema comes from the `search_path` of
   `CANOA_SQLALCHEMY_DATABASE_URI` (`?options=-csearch_path%3Dcanoa_dev`) or from the role's
   default (`ALTER ROLE canoa_connstr IN DATABASE adaptabrasil SET search_path=canoa;`).
   A Windows copy of the DB, for example, is `canoa_dev` while a plain run means Production.
   For local work set `CANOA_APP_MODE=Development` or `CANOA_DEBUG=True`.

`CANOA_DEBUG` does not paint the badge red by itself: `CANOA_DEBUG="True"` on a Production
server only adds the `Debugging is ON on the production DB.` warning.

Quick check on a server: the startup log must say
`The 'fuse' was started in Production mode`, and `CANOA_DEBUG` must be absent or false.

## What flips when debugging is on

`DynamicConfig.__init__()` propagates `APP_DEBUG` into several Flask/Jinja sub-flags
*unless each one was already set explicitly* (`None` means "inherit"):
`TESTING`, `DEBUG_TEMPLATES`, `APP_MINIFY_OFF`, `APP_DISPLAY_DEBUG_MSG`,
`DEBUG_RENDERED_TEMPLATES`. `DEBUG_TEMPLATES` makes
[jinja_helper.py](../helpers/jinja_helper.py) validate the raw template before rendering;
`DEBUG_RENDERED_TEMPLATES` makes it scan the rendered HTML for duplicate ids and dump a
bugged copy to `log_files/`.

`sidekick.debugging` itself is checked directly in a few places:
- [base.py](../models/base.py) (`get_row`/`get_rows`) — raises if a requested column name
  doesn't exist on the table/view, instead of letting SQLAlchemy fail silently later.
- [ui_db_texts_manager.py](../helpers/ui_db_texts_manager.py) and the `ValidateProcessConfig`
  call sites ([process.py](../private/validate_process/process.py),
  [rv_process.py](../private/validate_process/rv_process.py),
  [revalidate_file.py](../private/revalidate_file.py),
  [receive_file.py](../private/receive_file.py)) — passed through so those subsystems can
  log/behave more verbosely.
- [pw_helper.py](../helpers/pw_helper.py)'s `internal_logout()` — skips the normal logout
  path when a power user is debugging (the UI-text-cache flush that belongs there is still
  a `# TODO`, commented out).

## `debug_info.py` — captured but not yet shown anywhere

[debug_info.py](../public/debug_info.py)'s `get_debug_info()` builds a table (app version,
mode, `APP_DEBUGGING`, DB URI, Flask/SQLAlchemy/Jinja2 versions, etc.) and `main.py` calls it
when `APP_DISPLAY_DEBUG_MSG` is on — but the result is only ever assigned to a local `di`
variable (`# TODO, print`). There is no page or log line that surfaces it yet; wiring it up
(a route, a footer, a log dump) is still open.

---
<small>_eof_</small>
