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
APP_VERSION = "β 6.01"  # 2026-08-19

# default user HTML/DB lang/locale (see table users.lang)
APP_LANG = "pt-br"

# the file that displays handled exceptions (see \helpers\jinja_helper.py)
APP_UPS_HTML_PAGE_FILE_NAME = "ups_page.html.j2"

# Message error for a jinja leftover tag
APP_JINJA_TEMPLATE_BUG_FOUND = "🚨 A Jinja runtime error was detected"
APP_JINJA_TEMPLATE_BUG_MSG_TECH = "Disable config.DEBUG_RENDERED_TEMPLATES to hide this error."


APP_RAW_HTTP_ERROR_RAISED = "raw_http_error_raised"

# Cookie name set on every file-download response (spd_download.py, sep_ids_download.py,
# scm_export_db.py, received_files/download_record.py) so canoa.js's setSleepVeil() can poll
# for it instead of guessing a fixed delay. Keep in sync with canoa.js's own copy of this
# string -- it's a static JS file, not Jinja-rendered, so it can't import this constant.
APP_DOWNLOAD_READY_COOKIE = "download_ready"

# /docs/<publicDocName> names reachable without login (public/routes.py's docs() route)
PUBLIC_DOC_NAMES = ("privacyPolicy", "termsOfUse")

# eof
