# Equipe da Canoa -- 2024
#
#
# mgd 2024-04-08

# cSpell:ignore

import os
from bs4 import BeautifulSoup
from flask import current_app
from typing import cast, List

URL_PATH_SEP: str = "/"


def url_join(*args: str) -> str:
    """
    Joins URL components into a single URL path, ensuring proper formatting.

    Args:
        *args (str): URL components to be joined.

    Returns:
        str: The joined URL path.
    """
    return URL_PATH_SEP.join(arg.strip(URL_PATH_SEP) for arg in args)


def icon_url(file_name: str) -> str:
    """
    Constructs the full URL path for an icon image to be used in an HTML img tag.

    Args:
        folder (str): The sub folder (of the static folder) where the icon image is located
        file_name (str): The name of the icon image file.

    Returns:
        str: The full URL path of the icon image.
    """
    base_path = os.path.basename(cast(str, current_app.static_folder))
    icon_url = URL_PATH_SEP + url_join(base_path, "icons", file_name)
    return icon_url


def icon_svg_inline(svg_file_path: str) -> str:
    """Load an SVG file for inline HTML embedding.

    Strips the XML declaration, adds a viewBox derived from the fixed dimensions
    if one is absent, then replaces fixed width/height with 100% so the parent
    element controls the rendered size.
    Returns an empty string on any error.
    """
    import re

    try:
        with open(svg_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        content = re.sub(r"<\?xml[^>]+\?>\s*", "", content)

        def _fix_svg_tag(m: re.Match) -> str:
            tag = m.group(0)
            if "viewBox" not in tag:
                w = re.search(r'\bwidth="(\d+)"', tag)
                h = re.search(r'\bheight="(\d+)"', tag)
                if w and h:
                    tag = tag[:-1] + f' viewBox="0 0 {w.group(1)} {h.group(1)}">'
            tag = re.sub(r'\bwidth="[^"]*"', 'width="100%"', tag)
            tag = re.sub(r'\bheight="[^"]*"', 'height="100%"', tag)
            return tag

        content = re.sub(r"<svg\b[^>]*>", _fix_svg_tag, content, count=1)
        return content.strip()
    except Exception:
        return ""


def img_change_src_path(html_content: str, new_img_folder: list) -> str:
    # Change img tag `src` path to a new_img_path & return the modified html
    import os
    import re

    soup = BeautifulSoup(html_content, "html.parser")
    img_tags = soup.find_all("img")

    for img_tag in img_tags:
        src = img_tag.get("src", "")  # type: ignore
        if src:
            _, image_name = re.match(r"(.*/)(.*)", src).groups()  # type: ignore (to much error for a r)
            img_folder = new_img_folder.copy()
            img_folder.append(image_name)
            image_path = os.path.join(*img_folder)
            img_tag["src"] = image_path  # type: ignore  /check the docs

    return str(soup)


# Returns a list of all img tag `src` filename
def img_filenames(html_content: str) -> List[str]:
    from .file_helper import file_full_name_parse

    soup = BeautifulSoup(html_content, "html.parser")
    img_tags = soup.find_all("img")
    images: List[str] = []
    for img_tag in img_tags:
        src = cast(str, img_tag.get("src", ""))  # type: ignore  /check the docs
        if src:
            _, _, filename = file_full_name_parse(src)
            images.append(filename)

    return images


# eof
