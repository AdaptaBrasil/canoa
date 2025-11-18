"""
local_ui_texts.py

A dictionary of texts for the user interface in
case the database connection fails

Equipe Canoa -- 2025

mgd 2025-03-15, 5-23
"""

# cspell:words Entendí ui_texts_locale

from ..helpers.ui_db_texts_helper import ui_texts_locale, UITextsKeys

default_locale = "en"
default_section = "Form"
error_text = "Text"

class AuxTexts:
    section = "AuxTexts"
    techIntro = "techIntro"


class Locale:
    # text in lower case
    br = "pt-br"
    en = "en"
    es = "es"


local_texts = {
    Locale.br: {
        default_section: {
            UITextsKeys.Form.title: "Situação Inesperada",
            UITextsKeys.Form.date_format: "pt-br",
            UITextsKeys.Form.btn_close: "Entendi",
            UITextsKeys.Form.icon_file: "ups_handler.svg",
        },
        UITextsKeys.Fatal.no_db_conn: {
            UITextsKeys.Msg.warn: "Houve um erro e não foi possível conectar ao banco de dados. Por favor, tente novamente mais tarde."
        },
        AuxTexts.section: {
            AuxTexts.techIntro: "Por favor, informe este texto: '{0}'",
        }
    },
    Locale.en: {
        default_section: {
            UITextsKeys.Form.title: "Unexpected Situation",
            UITextsKeys.Form.date_format: "en",
            UITextsKeys.Form.btn_close: "OK",
            UITextsKeys.Form.icon_file: "ups_handler.svg",
        },
        UITextsKeys.Fatal.no_db_conn: {
            UITextsKeys.Msg.warn: "There was an error and it was not possible to connect to the database. Please try again later."
        },
        AuxTexts.section: {
            AuxTexts.techIntro: "Por favor informe este texto: '{0}'",
        }
    },
    Locale.es: {
        default_section: {
            # cSpell:ignore posible conectarse datos  inténtelo nuevo Situación
            UITextsKeys.Form.title: "Situación Inesperada",
            UITextsKeys.Form.date_format: "es",
            UITextsKeys.Form.btn_close: "Entendí",
            UITextsKeys.Form.icon_file: "ups_handler.svg",
        },
        UITextsKeys.Fatal.no_db_conn: {
            UITextsKeys.Msg.warn: "Hubo un error y no fue posible conectarse a la base de datos. Por favor, inténtelo de nuevo más tarde."
        },
        AuxTexts.section: {
            AuxTexts.techIntro: f"Por favor, reporte este texto: '{0}'",
        }
    },
}


def _get_ui_texts(section):
    locale = ui_texts_locale().lower()
    ui_sections = local_texts.get(locale, {})

    if not ui_sections:
        locale_mayor = ui_texts_locale().split("-")[0]
        ui_sections = local_texts.get(locale_mayor, {})

    if not ui_sections:
        ui_sections = local_texts.get(default_locale, {})

    ui_texts = ui_sections.get(section, {})
    return ui_texts


# generic
def local_ui_texts(section):
    ui_texts = _get_ui_texts(section)

    return ui_texts


# for ui_form_texts()
def local_form_texts():
    ui_form_texts = _get_ui_texts(default_section) or {}

    return ui_form_texts


# eof
