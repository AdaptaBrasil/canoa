#
#
# mgd 2024-06-21

# cSpell:ignore tpmt

from flask import current_app, render_template
from typing import Any

from .py_helper import as_str_strip

from ..helpers.types_helper import jinja_template


# mark a string as a jinja text, a text that will be parsed before rendering
_jinja_pre_template_mark = "^"


def prepare_template(tpmt: jinja_template) -> jinja_template:
    prepared = tpmt.strip()

    return prepared


def jinja_pre_template(val: str) -> str:
    # mgd 2024-06-21, not ready
    text = val
    try:
        # Create a template from the value
        template = current_app.jinja_env.from_string(val)
        text = template.render()
    except Exception as e:
        print(f"Error rendering template [{val}]: {e}")

    return text


def process_pre_templates(texts: dict, mark: str = _jinja_pre_template_mark):
    """
    Process the dictionary to apply _jinjaText where necessary
    Original idea by mgd

    Example:
        # A typical jinja texts to use on a template, except for `About`,
        # that starts and ends with the (default) jinja_template_mark: ^
        texts = {
            'fruit': 'lucuma'
            , 'stone': 'meteoric'
            , 'about': '^About {{ app_name }} version {{ app_ver }}^'
        }
        processed_texts = process_pre_templates(texts)
        print(processed_texts['about']) # -> "About Canoa version 21.8"
    """
    for key, text in texts.items():
        if len(text) > 7 and text[0] == mark and text[0] == text[-1]:
            pre_template = text.strip(mark)
            value = jinja_pre_template(pre_template)
            texts[key] = value
    return texts


def process_template(tmpl_ffn: str, **context: Any) -> str:
    """
    TODO check if in debug HTML
    TODO  » basic jinja errors if in debug
    TODO  » HTML with BeautifulSoup
    """

    tmpl = render_template(tmpl_ffn, **context)
    tmpl_s = as_str_strip(tmpl)
    return tmpl_s


# eof
