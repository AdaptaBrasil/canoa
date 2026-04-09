# Equipe da Canoa -- 2024
#
# Password Helpers
#


# cSpell:ignore urandom pwdhash hexlify dopwh


import os
import hashlib
import binascii
from flask_login import current_user


class Codec:
    utf_8 = "utf-8"
    ascii = "ascii"


def __dopwh(text: str, salt: str) -> bytes:
    pwd_digest = hashlib.pbkdf2_hmac("sha512", text.encode(Codec.utf_8), salt.encode(Codec.ascii), 100000)
    pwd_hashed = binascii.hexlify(pwd_digest)
    return pwd_hashed


# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/


def hash_password(user_password: str) -> bytes:
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest()
    pwd_hashed = __dopwh(user_password, salt)
    return salt.encode(Codec.ascii) + pwd_hashed  # return bytes


# def verify_pass1(provided_password: str, stored_password: str) -> bool:
#     # Verify a stored password against one provided by user
#     stored_password = stored_password.decode(Codec.ascii)
#     salt = stored_password[:64]
#     stored_password = stored_password[64:]
#     pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode(Codec.utf_8), salt.encode(Codec.ascii), 100000  )
#     pwdhash = binascii.hexlify(pwdhash).decode(Codec.ascii)
#     return pwdhash == stored_password


def verify_password(provided_password: str, stored_password: bytes) -> bool:
    """Verify a stored password against one provided by user."""
    stored_password_str = stored_password.decode(Codec.ascii)
    salt = stored_password_str[:64]
    stored_pwd_hash = stored_password_str[64:]
    provided_pwd_hash = __dopwh(provided_password, salt).decode(Codec.ascii)
    return stored_pwd_hash == provided_pwd_hash


def is_anyone_logged() -> bool:

    anyone_logged = False
    try:
        anyone_logged = False if current_user is None else current_user.is_authenticated and (current_user.id > 0)
    except:
        anyone_logged = False

    return anyone_logged


def nobody_is_logged() -> bool:
    return not is_anyone_logged()


def internal_logout():
    from ..common.app_context_vars import sidekick, app_user
    from flask_login import logout_user

    if not is_anyone_logged():
        pass
    elif sidekick.debugging and app_user.is_power:
        # TODO from ..helpers. import UITexts_Cache
        # UITexts_Cache.flush()
        #sidekick.display.info(f"{UITexts_Cache.__name__} flushed.")
        logout_user()
    else:
        logout_user()

    return


# eof
