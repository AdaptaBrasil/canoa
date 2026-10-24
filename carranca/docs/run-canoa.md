# Canoa Screen Commands

```screen``` refers to the Linux command-line tool GNU Screen, a terminal multiplexer.

It allows you to:
   - Start a command (like flask run)
   - Detach from it and close your SSH/RDP session
   - Reattach later and continue exactly where you left off
   - -Keep long-running processes alive even if your connection drops

GNU Screen is not a windowing system nor physical terminal. It is a software tool that creates “virtual terminals” inside your real terminal.

## Start Canoa (in a screen session)

1. Check no Canoa session is already running:
   ```
   screen -ls
   ```
2. If one is active, kill it (replace `12345` with the actual session id):
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
```
screen -r canoa
```

## Attach to an attached (by someone else: Detach-Reattach) screen session
```
screen -dr 123456.canoa
```

## Kill a screen session
Outside screen:
```
screen -S canoa -X quit
```

Inside screen:
Press: Ctrl + A then K, confirm with y

## Kill running Canoa processes
```
ps aux | grep flask
kill -9 <PID>
```

## Kill running Canoa processes


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

1. `_get_debug_2()` ([igniter.py](../common/igniter.py)) reads the `CANOA_DEBUG` env var
   (`get_envvar("debug", ...)` prefixes it with `CANOA_`) via `as_bool()`. Config and code
   defaults are skipped here on purpose — see the "Considerations" comment next to it; at
   this point no config has been selected yet, so there is nothing to default from.
2. `Args(debug_2).from_arguments()` ([Args.py](../common/Args.py)) seeds `app_debug` from
   that env value, then `set_flags_from_argv()` lets a `--app_debug` command-line flag
   override it (any attribute of `Args` can be forced `True` this way by name).
3. `Fuse.debugging = args.app_debug` ([igniter.py](../common/igniter.py)).
4. Once the app mode (`Development` / `Stage` / `Production`) picks a config class
   ([DynamicConfig.py](../config/DynamicConfig.py)), `_ignite_config()` sets:
   `config.APP_DEBUGGING = True if fuse.debugging else config.APP_DEBUG`.
   So the CLI/env flag can force debug *on* in any mode, but it can never force it *off*
   in a mode whose own `APP_DEBUG` is `True` (only `DevelopmentConfig`/`StageConfig` default
   `APP_DEBUG` to `True`; `ProductionConfig` defaults it to `False`).
5. `Sidekick.debugging = bool(config.APP_DEBUGGING)` ([Sidekick.py](../common/Sidekick.py))
   is what the rest of the app actually reads at runtime.

⚠️ `igniter.py` repeats the warning inline: **don't run with debug turned on in production.**

## Turning it on locally

- VS Code: [launch.json](../../.vscode/launch.json)'s "Canoa" config already sets
  `CANOA_DEBUG=true` and `FLASK_DEBUG=1` as env vars for the debug session.
- Shell: `export CANOA_DEBUG="True"` before `../rema.sh` (see
  [canoa_env_vars.txt](../../canoa_env_vars.txt)). `FLASK_DEBUG` is Flask's own reloader/
  debugger switch and is independent from `CANOA_DEBUG` — Canoa's flag drives
  `config.APP_DEBUGGING`, not Flask's.
- CLI: pass `--app_debug` as an argument to `main.py`.

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
  [revalidate_sep.py](../private/revalidate_sep.py),
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
