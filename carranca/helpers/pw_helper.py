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


def __dopwh(text: str, salt: str) -> str:
    pwd_digest = hashlib.pbkdf2_hmac("sha512", text.encode(Codec.utf_8), salt.encode(Codec.ascii), 100000)
    pwd_hashed = binascii.hexlify(pwd_digest)
    return pwd_hashed


# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/


def hash_pass(user_password: str) -> str:
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


def verify_pass(provided_password: str, stored_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    stored_password = stored_password.decode(Codec.ascii)
    stored_pwd_hashed = stored_password[64:]
    provided_pwd_hashed = __dopwh(provided_password, stored_password[:64]).decode(Codec.ascii)
    return stored_pwd_hashed == provided_pwd_hashed


def is_someone_logged() -> bool:
    # mgd:
    # in some context, current_user is an 'invalid pointer'
    # from flask_login import current_user

    logged = False
    try:
        logged = False if current_user is None else current_user.is_authenticated and (current_user.id > 0)
    except:
        logged = False

    return logged


def nobody_is_logged() -> bool:
    return not is_someone_logged()


def internal_logout():
    from flask_login import logout_user

    if is_someone_logged():
        logout_user()
        
    return


# eof
