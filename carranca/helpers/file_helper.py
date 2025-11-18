"""
File helpers

Equipe da Canoa -- 2024
mgd
"""

import os
import shutil
from os import path, makedirs
from typing import Optional


def file_full_name_parse(file_full_name: str) -> tuple[str, str, str]:
    ''' split full path into 3 components:
        drive, path, filename '''
    drive, path = os.path.splitdrive(file_full_name)
    _, filename = os.path.split(path)
    return (drive, path, filename)


def path_remove_last_folder(dir: str) -> str:
    # remove the last folder form the path (~ cd..)
    folders = dir.split(path.sep)
    if len(folders) < 2:
        return None
    else:
        short_dir = path.sep.join(folders[:-1])
        return short_dir


def change_file_ext(file: str, ext: str = ""):
    """
    Changes the extension of a given file.

    Args:
        file: The original file name.
        ext: The new extension to be applied.
             Should include the dot (e.g., '.txt').
             If not provided, the extension is removed.

    Returns:
        The file name with the new extension.
    """
    root, _ = path.splitext(file)
    new_file = root + ext
    return new_file


def is_first_param_newer(newer_full_name: str, older_full_name: str) -> Optional[bool]:
    newer_stat = os.stat(newer_full_name) if path.isfile(newer_full_name) else None
    older_stat = os.stat(older_full_name) if path.isfile(older_full_name) else None

    if newer_stat is None or older_stat is None:
        return None
    else:
        return newer_stat.st_mtime > older_stat.st_mtime


def file_must_exist(
    file_full_name: str, source_full_name: str, replace_if_newer: bool = False
) -> bool:
    """
    Checks if a file exists and optionally replaces it if newer.

    Args:
        file_full_name: File to check
        source_file: The source file to copy or replace if newer
        replace_if_newer: If True, replaces the file if the source is newer

    Returns:
        True if the file was successfully replaced or copied, False otherwise.
    """
    source_exists = path.isfile(source_full_name)
    done = path.isfile(file_full_name)
    try:
        if done and not replace_if_newer:
            return True
        elif not source_exists:
            return False
        elif not done:
            shutil.copyfile(source_full_name, file_full_name)
        elif is_first_param_newer(source_full_name, file_full_name):
            os.remove(file_full_name)
            shutil.copyfile(source_full_name, file_full_name)
            shutil.copystat(source_full_name, file_full_name)

    except OSError as e:
        from ..common.app_context_vars import sidekick

        sidekick.app_log.error(
            f"Error {('replacing' if done else 'copying file')} [{source_full_name}] to [{file_full_name}]: {e}')"
        )
    finally:
        done = path.isfile(file_full_name)
    return done


def folder_must_exist(full_path: str) -> bool:
    done = path.isdir(full_path)
    try:
        if not done:
            makedirs(full_path)
            done = True
    except Exception as e:
        from ..common.app_context_vars import sidekick

        done = False
        sidekick.app_log.error(f"Error creating folder {full_path}, {e}")

    return done


def is_same_file_name(file1: str, file2: str):
    return path.normcase(file1) == path.normcase(file2)


# eof
