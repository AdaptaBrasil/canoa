"""
main.py
  Main Module following the Application Factory Pattern
  FLASK's APP

  Equipe da Canoa -- 2024
  mgd 2024-10-03
"""

# cSpell:ignore sqlalchemy cssless keepalives UNMINIFIED
from __future__ import annotations
from typing import cast, Tuple, TYPE_CHECKING
from flask_minify import Minify

if TYPE_CHECKING:
    from flask import Flask


def _init_minify(app: "Flask", config: str) -> Tuple[Minify | None, str]:
    from .helpers.py_helper import strip_and_ignore_empty

    cnf_str = " ".join(strip_and_ignore_empty(config))

    def _g(key) -> bool:
        return f" {key} ".lower() in f" {cnf_str} ".lower()

    error: str = ""
    minify = None
    try:
        minify = Minify(app=app, html=_g("html"), js=_g("js"), cssless=_g("css"))
    except Exception as e:
        error = str(e)
        minify = None

    return minify, error


import time
from .common.app_constants import APP_NAME, APP_VERSION

# -------------------------------------------------------
# Main --------------------------------------------------
# -------------------------------------------------------
# This should be the first message of this package
the_aperture_msg = f"{APP_NAME} is starting in {__name__}."
print(f"{'-' * len(the_aperture_msg)}\n{the_aperture_msg}")


# Flask app
from carranca import create_app, started  # see __init__.py
from .helpers.py_helper import is_str_none_or_empty

app, sidekick = create_app()

if sidekick.config.APP_MINIFY_OFF:
    sidekick.display.info("App minification is fully disabled.")
elif is_str_none_or_empty(modules := sidekick.config.APP_MINIFY_MODULES):
    sidekick.display.error(f"App minification requested but not configured in APP_MINIFY_MODULES.")
elif (result := _init_minify(app, modules)) and (m := result[0]):
    sidekick.display.info(f"Flask-Minify initialized: [html: {m.html}, js: {m.js}, cssless: {m.cssless}].")
else:
    error = result[1]
    sidekick.display.error(f"Configuration error: Flask-Minify raised an Error: [{error}].")
    # sidekick.display.info("Install with 'pip install Flask-Minify' or set APP_MINIFY_OFF=False in config.")


sidekick.display.info("The app is ready to run!")


if sidekick.config.APP_DISPLAY_DEBUG_MSG:
    # print(repr(sidekick))
    from .public.debug_info import get_debug_info

    di = get_debug_info(app, sidekick.config)  # TODO, print

# Tell everybody how quick we are
elapsed = (time.perf_counter() - started) * 1000
sidekick.display.info(f"{APP_NAME} version {APP_VERSION} is now ready for the journey.")
sidekick.display.debug(f"It took {elapsed:,.0f} ms to create and initialize it.")

# printed messages ;—)
try:
    _k = sidekick.display.Kind
    sidekick.display.set_elapsed_output(False)
    info = ""  # _k.USER,
    for k in [_k.INFO, _k.WARN, _k.ERROR, _k.DEBUG, _k.FATAL]:
        info += cast(str, sidekick.display.print(k, str(sidekick.occurrences(k)), "", True, True)) + ", "

    sidekick.display.set_elapsed_output(True)
    sidekick.display.info("Messages printed:  " + info.strip(", "))
    if (i := sidekick.occurrences(_k.ERROR)) > 1:
        sidekick.display.error(f"Attention: {i} errors occurred during initialization.")
finally:
    sidekick.display.set_elapsed_output(True)
    sidekick.display.restart_occurrences()


# -------------------------------------------
# (i)
# -------------------------------------------
# on the server, __name__ is 'carranca.main'
# the app is executed by
# `canoa/.vscode/launch.json`

app_debug = sidekick.config.APP_DEBUG
app_reload = sidekick.config.APP_AUTO_RELOAD
if __name__ != "__main__":
    sidekick.display.info("Using configuration from `.vscode/launch.json`.")
    sidekick.display.warn("This module is *not* running as `__main__`, so the app will not automatically run.")
else:
    app.run(debug=app_debug)

# TODO use watchfiles to reload the app
# elif if app_debug and not

#     if sidekick.config.APP_AUTO_RERUN and app_debug:
#         sidekick.display.warn(
#             "You are running the app with both debug and auto-reload. This is not recommended."
#         )
#     app.run(debug=app_debug)

# eof
