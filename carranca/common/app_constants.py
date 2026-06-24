"""
app_constants.py
  App Constants

  Equipe da Canoa -- 2024
  mgd 2024-10-03
"""

# Here and only here: the APP_NAME and APP_VERSION
# and avoid:
#  - attempted relative import with no known parent package
#  - circular..
#  &
#  - modify BaseConfig.py file each version change

APP_NAME = "Canoa"

# &beta; major.minor
APP_VERSION = "β 5.11"  # 2026-06-24

# default user HTML/DB lang/locale (see table users.lang)
APP_LANG = "pt-br"

# the file that displays handled exceptions (see \helpers\jinja_helper.py)
APP_UPS_HTML_PAGE_FILE_NAME = "ups_page.html.j2"

# Message error for a jinja leftover tag
APP_JINJA_TEMPLATE_BUG_FOUND = "🚨 A Jinja runtime error was detected"
APP_JINJA_TEMPLATE_BUG_MSG_TECH = "Disable config.DEBUG_RENDERED_TEMPLATES to hide this error."

# eof
