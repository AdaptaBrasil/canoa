# Equipe da Canoa -- 2024
# Publicly Shared Files Download
#
# inspired in
# https://stackoverflow.com/questions/38511444/python-download-files-from-google-drive-using-url
# mgd 2024-08-01

# cSpell:ignore puremagic surl googleapiclient gserviceaccount

import requests
import puremagic
from os import path, rename

from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build

from ..common.app_context_vars import sidekick
from .py_helper import is_str_none_or_empty, to_str
from .file_helper import is_same_file_name, change_file_ext
from .html_helper import CONTENT_TYPE_HTML, URL_PATH_SEP


def download_public_file(url, filename, guess_extension_if_not_provided=True) -> int:
    """
    Downloads a publicly shared Google Drive file.

    Args:
        url: The public shareable link of the file.
        filename: The desired filename for the downloaded file (extension is optional)
            guess_extension_if_not_provided: if True, the file contents will be analyzed
            to infer the extension if not is provided in the filename.
            If filename ends with a folder separation, the name is inferred of created

    Example:
        download_public_file(
            "https://drive.google.com/file/d/1iXyDi-NcGIobY0NY-fOQ34Ew-gcS0PzY/view?usp=sharing",
            "file_90202"  | "upload_files/"
        )
    """

    task_code = 0
    status = ""
    new_filename = filename
    try:
        task_code += 1
        if is_str_none_or_empty(url):
            return task_code

        task_code += 1
        file_id = get_file_id_from_url(url)
        if is_str_none_or_empty(file_id):
            return task_code

        task_code += 1
        response = requests.get(url, stream=True)

        task_code += 1
        status = f"Status: {response.status_code}, "
        response.raise_for_status()  # Raise an exception for error HTTP statuses
    except requests.exceptions.RequestException as e:
        sidekick.app_log.error(
            f"Could not get file from link [{url}]: {status}code {task_code}, error [{e}]."
        )
        return task_code

    try:
        task_code += 1
        _, file_ext = path.splitext(filename)
        ext_is_empty = is_str_none_or_empty(file_ext)
        # is_folder = filename.endswith(path.sep)
        rename_it = guess_extension_if_not_provided and ext_is_empty

        task_code += 1
        code_offset = 0
        code = 0
        content_type = response.headers.get("Content-Type", "")
        if CONTENT_TYPE_HTML in content_type:
            code_offset = 10
            code = download_public_google_file(file_id, filename, rename_it)
        else:
            code_offset = 20
            code = download_response(response, filename, rename_it)

        task_code = 0 if code == 0 else code + code_offset
        if task_code > 0:
            raise RuntimeError(f"Fault from '{content_type}'.")
        sidekick.display.info(
            f"The file from the link {url} of type '{content_type}' was successfully retrieved and saved to [{new_filename}]."
        )

        return 0
    except Exception as e:
        sidekick.app_log.error(
            f"Could not get file from link [{url}]: {status}code {task_code}, error [{e}]."
        )
        return task_code


def get_file_id_from_url(url: str) -> str:
    """Extracts the file ID from a Google Drive shared link."""
    id = None
    surl = to_str(url)
    parts = surl.split(URL_PATH_SEP)
    try:
        id = parts[parts.index("d") + 1]
    except ValueError:
        id = None  # || pass

    if id is None:
        from urllib.parse import urlparse, parse_qs

        purl = urlparse(surl)
        qs = parse_qs(purl)
        id = qs["id"]

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
    except Exception as e:
        sidekick.app_log.error(f"Could save file  [{filename}], error [{e}].")
        return task_code


def download_public_google_file(file_id, file_folder):

    def get_file_metadata(service, file_id):
        file_md = service.files().get(fileId=file_id).execute()
        return file_md

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    SERVICE_ACCOUNT_FILE = path.join(
        sidekick.config.LOCAL_STORAGE_PATH,
        "canoa-download-key.json",
    )

    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    service = build("drive", "v3", credentials=credentials)

    # How to get the file ID:
    # file_md = get_file_metadata(service, file_id)
    # file_name = file_md["name"]
    # destination_path = file_name  # Or specify a custom path

    request = service.files().get_media(fileId=file_id)

    fh = open(file_folder, "wb")
    try:
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            sidekick.display.debug(
                "download: progress %d%%." % int(status.progress() * 100)
            )
    finally:
        fh.close()


# eof
