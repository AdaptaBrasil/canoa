"""
*Display HTM File*
Reformats an HTML from the DB:
    - header
    - body
    - images
using `docName` as a section in
the db.view vw_ui_texts

Equipe da Canoa -- 2024
mgd
"""

# cSpell:ignore tmpl updt

import os
import base64

from typing import List
from ..common.UIDBTexts import UITextsKeys
from ..helpers.py_helper import is_str_none_or_empty
from ..public.ups_handler import get_ups_jHtml
from ..helpers.file_helper import folder_must_exist
from ..helpers.route_helper import init_response_vars
from ..helpers.html_helper import img_filenames, img_change_src_path
from ..helpers.jinja_helper import process_template, process_text
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import ModuleErrorCode, AppStumbled
from ..helpers.ui_db_texts_manager import init_ui_db_texts  # , set_msg_error, get_section, UITextsKeys


def __prepare_img_files(html_images: List[str], db_images: List[str], img_local_path: str, section: str) -> bool:
    from ..helpers.ui_db_texts_manager import db_retrieve_text

    is_img_local_path_ready = os.path.exists(img_local_path)
    missing_files = html_images.copy()  # missing files from folder, assume all

    for file_name in html_images:
        if is_img_local_path_ready and os.path.exists(os.path.join(img_local_path, file_name)):
            missing_files.remove(file_name)  # this img is not missing.

    if not folder_must_exist(img_local_path):
        sidekick.display.error(f"Cannot create folder [{img_local_path}] to keep the HTML's images.")
        return False

    # folder for images & a list of missing_files, are ready.
    # available_files are files that are not on the file system,
    #   but can be retrieved from the DB (db_images says so)
    available_files = [file for file in missing_files if file in db_images]
    # TO USE repairable_files = len(available_files) - len(missing_files)
    if len(missing_files) == 0:
        return True  # every file is in file system!

    elif len(available_files) == 0:
        q = len(missing_files)
        qtd = "One" if q == 1 else f"{q}"
        p = "" if q == 1 else "s"
        sidekick.display.warn(f"{qtd} image record{p} missing for [sectorSpecifications] in database: {', '.join(missing_files)}.")
        return True  # some files missing, but I can't fix it :-(

    for file in available_files:
        try:
            b64encoded = db_retrieve_text(file, section)
            if not is_str_none_or_empty(b64encoded):
                image_data = base64.b64decode(b64encoded)
                with open(os.path.join(img_local_path, file), "wb") as file:
                    file.write(image_data)
        except Exception as e:
            sidekick.display.error(f"Error writing image [{file}] in folder {img_local_path}. Message [{str(e)}]")

    return True

    # ============= Documents ============== #
    # TODO:
    #    1. Move path to ...
    #    1. Only show Public docs if not logged.
    #    2. check if body exists else error


def display_html(docName: str):

    tmpl_ffn = "./home/document.html.j2"
    section = docName
    jHtml, _, default_texts, task_code = init_response_vars(ModuleErrorCode.DISPLAY_HTML_DOC)

    try:
        default_texts = init_ui_db_texts("DisplayDoc")  # default section
        ui_db_texts = init_ui_db_texts(section)

        def _updt_val(key: str, default: str):
            if not ui_db_texts.get_str(key):
                value = default_texts.get_str(key, default)
                ui_db_texts.set_value(key, value)
            return

        _updt_val(UITextsKeys.Page.title, "Display Document")
        _updt_val(UITextsKeys.Form.title, "Document")
        _updt_val(UITextsKeys.Form.btn_close, "Close")
        _updt_val("documentStyle", "")

        # shortcuts
        task_code += 1
        body_key = "documentBody"
        body_raw = ui_db_texts.get_str(body_key)
        body_proc = process_text(body_raw, **ui_db_texts.data())
        body_text = ui_db_texts.set_value(body_key, body_proc)

        images = ui_db_texts.get_str("images")

        # a comma separated list of images.ext names available on the db,
        # see below db_images & _prepare_img_files
        task_code += 1
        db_images = [] if is_str_none_or_empty(images) else [s.strip() for s in images.split(",")]  # list of img names in db

        task_code += 1  # 173
        html_images = [] if is_str_none_or_empty(body_text) else sorted(img_filenames(body_text))  # list of img tags in HTML

        task_code += 1
        img_folders = ["static", "docs", section, "images"]
        img_local_path = os.path.join(sidekick.config.APP_FOLDER, *img_folders)
        task_code += 1
        if is_str_none_or_empty(body_text):
            task_code += 1
            _, msg = default_texts.set_msg_error("documentNotFound", docName)
            raise AppStumbled(msg, task_code, False, True)
        elif len(html_images) == 0:
            # html has no images
            task_code += 2
            pass
        elif len(db_images) == 0:
            # if any images are missing in the folder,
            # I can't help, no images found in db
            # TODO: have a not_found_image.img
            pass
        elif __prepare_img_files(html_images, db_images, img_local_path, section):
            task_code += 3
            img_folders.insert(0, os.sep)
            doc_body_with_imgs = img_change_src_path(body_text, img_folders)
            ui_db_texts.set_value(body_key, doc_body_with_imgs)

        jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

    except Exception as e:
        jHtml = get_ups_jHtml("displayDocException", default_texts, task_code, e)

    return jHtml


# eof
