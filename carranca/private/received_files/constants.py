"""
User's Received Files's Management

Common constants and functions

Equipe da Canoa -- 2025
mgd 2025-01-14 & 03-18
"""

# Don't repeat constants
DOWNLOAD_REPORT = "R"   # Report
DOWNLOAD_ZIPFILE = "F"  # File

# see column user_data_files.file_origin:char(1)
#  » Indicates the source of the uploaded file, with
#       'L' for local uploads and
#       'C' for cloud downloads.
#       'S' for a stored file, revalidated (kept in the uploaded folder).
FILE_ORIGIN_LOCAL = "L"
FILE_ORIGIN_CLOUD = "C"
FILE_ORIGIN_STORAGE = "S"


# eof
