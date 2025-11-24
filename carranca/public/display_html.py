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

# cSpell:ignore tmpl

import os
import base64

from flask import render_template

from ..common.UIDBTexts import UIDBTexts
from ..helpers.py_helper import is_str_none_or_empty
from ..public.ups_handler import get_ups_jHtml
from ..helpers.file_helper import folder_must_exist
from ..helpers.route_helper import init_response_vars
from ..helpers.html_helper import img_filenames, img_change_src_path
from ..helpers.jinja_helper import process_template, jinja_pre_template
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import ModuleErrorCode, AppStumbled
from ..helpers.ui_db_texts_helper import add_msg_error, get_section, UITextsKeys


def __prepare_img_files(html_images: list[str], db_images: list[str], img_local_path: str, section: str) -> bool:
    from ..helpers.ui_db_texts_helper import retrieve_text

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
        sidekick.display.warning(
            f"{qtd} image record{p} missing for [sectorSpecifications] in database: {', '.join(missing_files)}."
        )
        return True  # some files missing, but I can't fix it :-(

    for file in available_files:
        try:
            b64encoded = retrieve_text(file, section)
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
    task_code = ModuleErrorCode.DISPLAY_HTML_DOC
    tmpl_rfn = "./home/document.html.j2"
    section = docName
    jHtml, _, ui_db_texts = init_response_vars()

    try:

        def _get_section(ui_section: str) -> UIDBTexts:
            ui_texts = get_section(ui_section)
            return UIDBTexts(ui_texts, sidekick.debugging)

        ui_db_texts = _get_section("DisplayDoc")
        doc_texts = _get_section(section)

        def _setValue(key: str, default: str):
            value = doc_texts.get_str(key)
            if not value:
                value = ui_db_texts.get_str(key, default)
                doc_texts[key] = value
            return

        _setValue(UITextsKeys.Page.title, "Display Document")
        _setValue(UITextsKeys.Form.title, "Document")
        _setValue(UITextsKeys.Form.btn_close, "Close")
        _setValue("documentStyle", "")

        # shortcuts
        task_code += 1
        body_key = "documentBody"
        body = doc_texts.get_str(body_key)
        images = doc_texts.get_str("images")

        # a comma separated list of images.ext names available on the db,
        # see below db_images & _prepare_img_files
        task_code += 1
        db_images = (
            [] if is_str_none_or_empty(images) else [s.strip() for s in images.split(",")]
        )  # list of img names in db

        task_code += 1  # 173
        html_images = [] if is_str_none_or_empty(body) else sorted(img_filenames(body))  # list of img tags in HTML

        task_code += 1
        img_folders = ["static", "docs", section, "images"]
        img_local_path = os.path.join(sidekick.config.APP_FOLDER, *img_folders)
        task_code += 1
        if is_str_none_or_empty(body):
            task_code += 1
            msg = add_msg_error("documentNotFound", ui_db_texts, docName)
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
            body = img_change_src_path(body, img_folders)

        doc_body = jinja_pre_template(body)
        doc_texts[body_key] = doc_body
        jHtml = process_template(tmpl_rfn, **doc_texts.dict())

    except Exception as e:
        jHtml = get_ups_jHtml("displayDocException", ui_db_texts, task_code, e, task_code)

    return jHtml


# eof
