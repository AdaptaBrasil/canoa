"""
 main.py
   Main Module following the Application Factory Pattern

   Equipe da Canoa -- 2024
   mgd 2024-10-03
"""

# cSpell:ignore sqlalchemy keepalives psycopg2

import time
from carranca.app_constants import app_name

# -------------------------------------------------------
# Main --------------------------------------------------
# -------------------------------------------------------
# This should be the first message of this package
the_aperture_msg = f"{app_name} is starting in {__name__}."
print(f"{'-' * len(the_aperture_msg)}\n{the_aperture_msg}")


# Flask app
from carranca import create_app, started  # see __init__.py

app, sidekick = create_app()

sidekick.display.info("All mandatory information has been checked and is available.")
sidekick.display.info("The app is ready to run!")


if sidekick.config.APP_DISPLAY_DEBUG_MSG:
    # print(repr(sidekick))
    from carranca.public.debug_info import get_debug_info

    di = get_debug_info(app, sidekick.config)  # TODO, print

# Tell everybody how quick we are
elapsed = (time.perf_counter() - started) * 1000
sidekick.display.info(
    f"{app_name} is now ready for the journey. It took {elapsed:,.0f}ms to create and initialize it."
)

if __name__ == "__main__":
    app.run()
    # TODO
    # from werkzeug.serving import run_simple
    # run_simple('localhost', 5000, app)
    # #

# eof
