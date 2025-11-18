"""
Equipe da Canoa -- 2024
Files Download: Google Drive (except zip) & others Publicly Shared Files

inspired in
https://stackoverflow.com/questions/38511444/python-download-files-from-google-drive-using-url

mgd 2024-08-01
"""

# cSpell:ignore puremagic surl googleapiclient gserviceaccount chunksize

import requests
import puremagic
import urllib.parse
from os import path, remove, rename


from .py_helper import is_str_none_or_empty, to_str
from .file_helper import is_same_file_name, change_file_ext
from ..common.app_context_vars import sidekick
from ..helpers.html_helper import URL_PATH_SEP


def is_url_valid(url: str) -> bool:
    try:
        urllib.parse.urlparse(url)
        return True
    except:
        return False


def is_gd_url_valid(url: str) -> int:
    result = 10
    if is_str_none_or_empty(url) or len(url) < 10:
        result = 1
    elif not url.lower().startswith("https://"):
        result = 2
    elif not is_url_valid(url):
        result = 3
    elif get_file_id_from_url(url) is None:
        result = 4
    else:
        result = 0

    return result


def get_file_id_from_url(url: str) -> str:
    """Extracts the file ID from a Google Drive shared link."""
    id = None
    surl = to_str(url)
    parts = surl.split(URL_PATH_SEP)
    if len(parts) < 3:
        return None
    try:
        id = parts[parts.index("d") + 1]
    except ValueError:
        id = None  # || pass

    if id is None:
        from urllib.parse import urlparse, parse_qs

        try:
            purl = urlparse(surl)
            qs = parse_qs(purl)
            id = qs["id"]
        except:
            id = None

    return id


def download_response(
    response: requests.Response, filename: str, rename_it: bool
) -> int:

    task_code = 1
    _, file_ext = path.splitext(filename)
    task_code = 2
    try:
        ext_found = not rename_it
        ext_by_magic = None
        with open(filename, "wb") as f:
            task_code = 4
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    task_code = 6
                    f.write(chunk)
                    task_code = 8
                    ext_by_magic = (
                        ext_by_magic if ext_found else puremagic.what(None, chunk)
                    )
                    ext_found = ext_found or bool(
                        ext_by_magic
                    )  # just try to find extension with the first `chunk`

        if rename_it and not is_same_file_name(to_str(ext_by_magic), file_ext):
            task_code = 9
            new_filename = change_file_ext(filename, ext_by_magic)
            rename(filename, new_filename)

        return 0
    except:  # Exception #as e:
        #   g.app_log.error(f"Could save file  [{filename}], error [{e}].")
        return task_code


def download_public_google_file(
    url_or_file_id: str,
    file_folder: str,
    file_name_format: str = "",
    del_file_if_exists: bool = True,
    debug: bool = False,
) -> tuple[int, str]:
    """Downloads a public Google file.
    Args:
        url_or_file_id: The URL or file ID of the Google file.
        file_folder: The folder where the downloaded file should be saved.
        file_mame_format: to modify original file name, eg '{0}003' or 'my_file_{0}'
        del_file_if_exists: Whether to delete the file if it already exists in the folder.

    Returns:
        A tuple containing:
            - The error code (0 if successful, non-zero if an error occurred).
            - The name of the downloaded file.
    """
    # Loading on demand this modules, will allow other upload methods to work

    try:
        from googleapiclient.http import MediaIoBaseDownload
        from googleapiclient.discovery import build
    except ImportError as e:
        raise ImportError("googleapiclient is required for Google Drive downloads. Please install it with 'pip install google-api-python-client'.") from e
    from google.oauth2.service_account import Credentials

    def get_file_metadata(service, file_id):
        file_md = service.files().get(fileId=file_id).execute()
        return file_md

    # local vars
    task_code = 1
    # Google Drive
    gdService = None
    gdFile_name = None
    gdFile_md = None  # google file metadata
    try:
        # Get file_id
        gdFile_id = None
        if is_str_none_or_empty(url_or_file_id) or len(url_or_file_id) < 10:
            task_code = 2
            raise ValueError(
                f"Invalid parameter value 'url_or_file_id' [{url_or_file_id}]]."
            )
        elif url_or_file_id.lower().startswith("https://"):
            task_code = 3
            gdFile_id = get_file_id_from_url(url_or_file_id)
        else:
            gdFile_id = url_or_file_id

        # file_id ready
        if not gdFile_id.replace("_", "u").replace("-", "m").isalnum():
            task_code = 4
            raise ValueError(f"Invalid value for file_id [{gdFile_id}].")
        elif not path.isdir(file_folder):
            task_code = 5
            raise ValueError(f"Invalid value for file_id [{gdFile_id}].")
        else:
            task_code = 6

        scope = ["https://www.googleapis.com/auth/drive.readonly"]

        service_account_file = path.join(
            sidekick.config.LOCAL_STORAGE_PATH,
            "canoa-download-key.json",
        )

        task_code += 1  # 7
        if not path.isfile(service_account_file):
            raise FileNotFoundError(service_account_file)

        task_code += 1  # 8
        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scope
        )

        task_code += 1  # 9
        gdService = build("drive", "v3", credentials=credentials)

        task_code += 1  # 10
        gdFile_md = get_file_metadata(gdService, gdFile_id)

        task_code += 1  # 11
        original_file_name = gdFile_md["name"]

        name, ext = path.splitext(original_file_name)
        if is_str_none_or_empty(file_name_format):
            gdFile_name = original_file_name
        elif "{0}" in file_name_format:
            gdFile_name = f"{file_name_format.format(name)}{ext}"
        elif "." in file_name_format:
            gdFile_name = original_file_name
        else:
            gdFile_name = original_file_name + ext

        file_full_path = (
            path.join(file_folder, gdFile_name)
            if not is_str_none_or_empty(file_folder)
            else gdFile_name
        )

        if not path.isfile(file_full_path):
            pass
        elif del_file_if_exists:
            task_code += 1  # 12
            remove(file_full_path)
            if path.isfile(file_full_path):
                PermissionError(file_full_path)
        else:
            task_code += 2  # 13
            FileExistsError(file_full_path)

        task_code += 3  # 14
        request = gdService.files().get_media(fileId=gdFile_id)

        task_code += 1  # 15
        with open(file_full_path, "wb") as f:
            task_code += 1  # 16
            cs = int(0 if not debug else 2 * 1024 * 1024)  # 2MB
            downloader = MediaIoBaseDownload(f, request, chunksize=cs)
            task_code += 1  # 17
            done = False
            sidekick.display.info(
                f"download: The download of the file [{file_full_path}] has begun."
            )
            # file_crc32 = crc32(b'')  # Initialize CRC32 checksum
            while done is False:
                status, done = downloader.next_chunk()
                # TODO find how: file_crc32 = crc32(status, file_crc32)
                if status:
                    sidekick.display.debug(
                        "download: progress %d%%." % int(status.progress() * 100)
                    )

        task_code = 0
        sidekick.display.info("download: The file was downloaded.")
    except Exception as e:
        msg_error = f"An error occurred while downloading the file. Task code {task_code}, message '{e}'.)"
        sidekick.display.error(msg_error)
        sidekick.app_log.error(msg_error)
    return task_code, gdFile_name, gdFile_md


# if __name__ == "__main__":
#     url = "https://drive.google.com/file/d/1m9crayVYtWXvkOPcQyzKQ2Eqme4jdkxX/view?usp=sharing"
#     grande = https://drive.google.com/file/d/14KkGgjb8gx-Yx5NJzrawJ-LcBhbxy9HM/view?usp=drive_link
#     download_public_google_file(url, "./uploaded_files/")


# eof
