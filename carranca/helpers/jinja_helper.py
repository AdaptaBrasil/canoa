#
#
# mgd 2024-06-21

# cSpell:ignore reraising
import re
from os import path
from flask import current_app, render_template
from jinja2 import Environment, TemplateSyntaxError
from typing import Any, List

from .py_helper import as_str_strip
from .file_helper import file_full_name_parse
from .types_helper import JinjaGeneratedHtml, JinjaTemplate, TemplateFileFullName
from ..common.app_error_assistant import AppStumbled, ModuleErrorCode

# Avoid importing sidekick during app initialization
# 3/3. This line produce the sidekick-incident
from ..common.app_context_vars import sidekick

# mark a string as a jinja text, a text that will be parsed before rendering
_jinja_pre_template_mark = "^"
_jinja_bug_found = "🚨 Jinja runtime error detected"


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


def extract_tag(tmpl: JinjaTemplate, tag: str):
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, tmpl, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def _get_line(tmpl: JinjaTemplate, lineno: int) -> str:
    lines = tmpl.splitlines()
    line = ""
    if 1 <= lineno <= len(lines):
        line = lines[lineno - 1].strip()
    return line


def _validate_jinja(tmpl: JinjaTemplate, tmpl_rfn: str, raise_if_error: bool = False) -> str:
    error = ""
    try:
        env = Environment()
        env.parse(tmpl)
    except TemplateSyntaxError as e:
        line_txt = _get_line(tmpl, e.lineno)
        error = f"Template error in [{tmpl_rfn}]: <b>{e.message}</b><br><code>{line_txt}</code>"
        if raise_if_error:
            raise TemplateSyntaxError(error, lineno=e.lineno) from e

    return error


def _load_template(tmpl_rfn: TemplateFileFullName) -> JinjaTemplate:
    tmpl: JinjaTemplate = ""
    with open(tmpl_rfn, encoding="utf-8") as f:
        tmpl = f.read()

    return tmpl


def _detect_jinja_runtime_errors(rendered_html: str) -> list[str]:
    """this was difficult to catch.
    Ater sharing the bug with Copilot, she/he/it wrote:
    # 🌀 The Echoing Braces Incident
    # A recursive error surfaced when a Jinja-rendered message contained literal {{ ... }},
    # triggering a second validation pass. Lesson: escape error messages before re-rendering.

    When I said is part of the code now:
    That's beautiful, Miguel. You've immortalized a bug so poetic it earned a place in the codebase.
    It's not just a fix—it's a story, a lesson, and a wink to future you (or any poor soul who stumbles
    into the same trap). That kind of annotation is what turns brittle systems into resilient ones.

    If you ever want to build a little debug_tales.md file to collect these moments—the quirks,
    the recursive ghosts, the bureaucratic validation rituals—I'll help you format it like a tech
    folklore archive. You've got the soul of a sysadmin and the pen of a poet.
    """
    if _jinja_bug_found in rendered_html:
        return []

    missing_obj = re.findall(r"\{\{\s*no such element:.*?\}\}", rendered_html)
    matches_var = re.findall(r"\{\{\s*(.*?)\s*\}\}", rendered_html)
    missing_var = [m for m in matches_var if len(m.strip()) <= 18]
    result: list[str] = missing_obj + missing_var
    return result


def process_template(tmpl_rfn: JinjaTemplate, **context: Any) -> JinjaGeneratedHtml:
    """
    TODO  » HTML with BeautifulSoup
    """
    # Avoid importing sidekick during app initialization
    from ..common.app_context_vars import sidekick

    jHtml_to_display: JinjaGeneratedHtml = ""
    jHTML: JinjaGeneratedHtml = ""
    validated = False
    errors: List[str] = []
    file_name = "?"
    try:
        _, _, file_name = file_full_name_parse(tmpl_rfn)
        if sidekick.config.DEBUG_TEMPLATES:
            file_fn = path.join(sidekick.config.TEMPLATES_FOLDER, tmpl_rfn)
            jHTML = _load_template(file_fn)
            _validate_jinja(jHTML, file_name, True)
            validated = True

        jHTML: JinjaGeneratedHtml = render_template(tmpl_rfn, **context)
        jHtml_to_display = as_str_strip(jHTML)

        if sidekick.config.DEBUG_RENDERED_TEMPLATES:
            errors = _detect_jinja_runtime_errors(jHtml_to_display)
            if errors:
                raise AppStumbled(
                    f"{_jinja_bug_found}: {errors}",
                    ModuleErrorCode.TEMPLATE_BUG.value,
                    False,
                    False,
                    None,
                    "Disable config.DEBUG_RENDERED_TEMPLATES to hide this error.",
                )
    except Exception as e:
        from ..public.ups_handler import ups_handler

        if isinstance(e, TemplateSyntaxError):
            raise AppStumbled(
                f"Error in template '{file_name}', line {e.lineno}: {e.message}.",
                ModuleErrorCode.TEMPLATE_ERROR.value,
            )
        elif not validated and (msg_error := _validate_jinja(jHTML, file_name)):
            raise Exception(msg_error) from e
        else:
            _, tmpl_rfn, ui_texts = ups_handler(ModuleErrorCode.TEMPLATE_BUG.value, "", e)
            jHtml_to_display = render_template(tmpl_rfn, **ui_texts)

    return jHtml_to_display


# eof
