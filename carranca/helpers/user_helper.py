"""
    Current User information helpers

    mgd
    Equipe da Canoa -- 2024
"""

# cSpell:ignore cuser mgmt

from os import path

from .py_helper import ms_since_midnight, to_base, now, crc16

_code_shift_id = 903
_ticket_receipt_sep = "_"


class UserFolders:
    common_folder = None
    downloaded = None
    uploaded = None

    def __init__(self):
        from ..Sidekick import sidekick

        UserFolders.common_folder = sidekick.config.COMMON_PATH

        def _common_user_folder(folder: str) -> str:
            return path.join(
                ("." if UserFolders.common_folder is None else UserFolders.common_folder),
                UserFolders.base_user_files,
                folder,
            )

        UserFolders.downloaded = _common_user_folder(UserFolders.base_downloaded)
        UserFolders.uploaded = _common_user_folder(UserFolders.base_uploaded)

    # this is a local folder to keep all uploaded files
    base_uploaded = "uploaded"
    # this is a local folder to keep all downloaded files
    base_downloaded = "downloaded"
    # this is a local for uploaded, downloaded & others users files
    base_user_files = "user_files"


def now_as_text() -> str:
    # current date time for user
    ##- TODO: get config <- from ui_texts
    return now().strftime("%d/%m/%Y às %H:%M")


def get_user_code(id: int) -> str:
    """
    generate a unique value for user (based in the user's table PK)
    for external use
    maxInt -> (2**53 - 1) -> 1F FFFF FFFF FFFF -> base 21=> 14f01e5ec7fda
    """
    return to_base(_code_shift_id + id, 21).zfill(5)


def get_user_folder(id: int) -> str:
    return get_user_code(id)


def get_file_ticket(user_code: str) -> str:
    """
        1    1  1   1           =  4  separators, _ (underscore) and - (for date)
    4    4    2  2  6           = 18
    0635_2024-04-30_abcdef      = 22

    4    : usuário
    _    : separador
    4-2-2: data yyyy-mm-dd
    _    : separador
    6    : ms do dia em base 22
    """
    # `user_receipt` (see below) dependes heavily in the format of the file_ticket
    ms = ms_since_midnight(True)  # max = ggi.48g = d86.400.000
    today_str = now().strftime("%Y-%m-%d")  # 4-2-2
    file_ticket = f"{user_code}{_ticket_receipt_sep}{today_str}{_ticket_receipt_sep}{ms}"
    return file_ticket


def get_unique_filename(name: str, ext: str = "") -> str:
    # https://strftime.org/
    today_str = now().strftime("%Y-%m-%d")  # 4-2-2_6
    ms = ms_since_midnight(True)
    filename = f"{name}{today_str}_{ms}{ext}"
    return filename


def get_user_receipt(ticket: str) -> str:
    """
    4-2-2: data yyyy-mm-dd
    _    : separador
    3    : crc16 of the `ticket`
    """
    crc = crc16(ticket)
    parts = ticket.split(_ticket_receipt_sep)
    receipt = f"{parts[1]}{_ticket_receipt_sep}{crc:04X}"
    return receipt


def get_batch_code() -> str:  # len 10
    from datetime import datetime

    _base = 22
    dt_from = datetime(2023, 12, 31)  # starting project date
    dt_diff = datetime.now() - dt_from
    days = dt_diff.days

    ms = ms_since_midnight(True)  # max = ggi.48g
    dy = to_base(days, _base).zfill(3)  # max= kkk => 10140/365= até 2050 ;-O
    batch_code = f"{dy}.{ms}"
    return batch_code


# eof
