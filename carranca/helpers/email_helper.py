"""
Equipe da Canoa -- 2024

Email Helpers & email providers Hub

mgd
2024-12-23, 2025-01-09, 2025-11-20 (hub)

"""

# cSpell:ignore SMTP

from enum import Enum
from typing import Optional
from .py_helper import as_str_strip, is_str_none_or_empty, strip_and_ignore_empty

# MIME _types
mime_types = {
    ".csv": "text/csv",
    ".htm": "text/html",
    ".html": "text/html",
    ".json": "application/json",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".xls": "Microsoft Excel 2007+",
    ".xlsx": "Microsoft Excel 2007+",
}


class EmailProvider(Enum):
    """
    Defines the valid backend email providers for the application.
    Using an Enum ensures constants are correctly recognized by the
    match/case statement and prevents 'name capture' errors.
    """

    NO_EMAIL = "No Email"
    SENDGRID = "SendGrid"
    GOOGLE = "GoogleApi"
    SMTP = "SMTP"


class RecipientsList:
    """
    email_or_recipients_list_items:
        email:
            email address to be used with second param 'name'
        email_or_recipients_list:
            a list of ; separated of RecipientsListItems

    """

    def __init__(self, email_or_recipients_list_items: str, name: str = ""):
        # TODO check if value has, at least, one e@mail.c
        param = ""
        if not name:
            items = email_or_recipients_list_items
            param = items
        else:
            email = email_or_recipients_list_items
            param = f"{as_str_strip(email)},{as_str_strip(name)}"

        self.as_str = param

    def list(self):
        return [] if is_str_none_or_empty(self.as_str) else strip_and_ignore_empty(self.as_str, ";")

    def parse(self, item: str):
        email, name = (item + ", ").split(",")[:2]
        return as_str_strip(email), as_str_strip(name)

    def __str__(self):
        return str(self.as_str)


class RecipientsDic:
    """
    Recipients to, cc, bcc as RecipientsList
    """

    def __init__(self, to: RecipientsList | str = "", cc: RecipientsList | str = "", bcc: RecipientsList | str = ""):
        def _set(rls: RecipientsList | str):
            if isinstance(rls, RecipientsList):
                return rls
            elif isinstance(rls, str):
                return RecipientsList(rls)
            else:
                return RecipientsList("")

        self.to = _set(to)
        self.cc = _set(cc)
        self.bcc = _set(bcc)


def send_email(
    send_to_or_dic: RecipientsList | RecipientsDic,
    texts_or_section: dict | str,
    body_params: Optional[dict] = None,
    file_to_send_full_name: Optional[str] = None,
    file_to_send_type: Optional[str] = None,
) -> bool:
    from ..common.app_context_vars import sidekick

    match sidekick.config.EMAIL_PROVIDER:
        case EmailProvider.SENDGRID.value:
            from .sendgrid_helper import _send_email

            return False

        case EmailProvider.GOOGLE.value:
            from .gmail_api_helper import _send_email

            return _send_email(send_to_or_dic, texts_or_section, body_params, file_to_send_full_name, file_to_send_type)

        case EmailProvider.SMTP.value:
            from .smtp_helper import _send_email

            return _send_email(send_to_or_dic, texts_or_section, body_params, file_to_send_full_name, file_to_send_type)

        case EmailProvider.NO_EMAIL:
            sidekick.display.debug("No email provider. Cannot sent email.")

        case _:
            raise KeyError(f"Unknown email provider [{sidekick.config.EMAIL_PROVIDER}].")


# eof
