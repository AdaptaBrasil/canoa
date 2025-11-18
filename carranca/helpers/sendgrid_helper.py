"""
Email helper, based in sendgrid API

Equipe da Canoa -- 2024

mgd
2024-05-10... 2025-01-09
"""

# pylint: disable=E1101
# cSpell:ignore sendgrid Heya

import sendgrid
from sendgrid.helpers.mail import Email, To, Cc, Bcc

from os import path
from typing import Callable, Optional, Type
from base64 import b64encode

from .py_helper import is_str_none_or_empty
from .email_helper import RecipientsDic, RecipientsListStr, mime_types
from .ui_db_texts_helper import get_section

# https://docs.sendgrid.com/pt-br/for-developers/sending-email/api-getting-started
# curl --request POST \
# --url https://api.sendgrid.com/v3/mail/send \
# --header 'Authorization: Bearer <<YOUR_API_KEY>>' \
# --header 'Content-Type: application/json' \
# --data '{"personalizations":[{"to":[{"email":"john.doe@example.com","name":"John Doe"}],"subject":"Hello, World!"}],"content": [{"type": "text/plain", "value": "Heya!"}],"from":{"email":"sam.smith@example.com","name":"Sam Smith"},"reply_to":{"email":"sam.smith@example.com","name":"Sam Smith"}}'

# https://stackoverflow.com/questions/40656019/python-sendgrid-send-email-with-pdf-attachment-file


# headers = {
#    'Authorization': f'Bearer {SENDGRID_API_KEY}',
#    'Content-Type': 'application/json',
# }
# response = requests.post('https://api.sendgrid.com/v3/mail/send', headers=headers, json=json_data)


def send_email(
    send_to_or_dic: RecipientsListStr | RecipientsDic,
    texts_or_section: dict | str,
    email_body_params: Optional[dict] = None,
    file_to_send_full_name: Optional[str] = None,
    file_to_send_type: Optional[str] = None,
) -> bool:
    """
        » Sends an email, handling both: string and dictionary formats for the recipient.

        » Takes the body text from the `vw_ui_texts` (view ui_texts_section) and
          replace it with email_body_params dictionary.

        » Sends an attached file when its path is specified `file_to_send_path`. If extension is is NOT a common
          file type (pdf, json, xlsx, txt, csv), please inform it in `file_to_send_type`

    Args:
        send_to_or_dic: (RecipientsListStr or RecipientsDic): The recipient information.
            If a RecipientsListStr is used, it's assumed to be the "to" recipient.
        texts_or_section: (dict or str)
            if str, is an entry of .ui_texts_helper.get_section that returns a dict
            if Dict[str, str], it is used directly.
            Expected dict Keys:
                subject=texts["subject"],
                html_content=texts["content"],
        email_body_params: Optional[ Dict[key: str, value: str] ]
            values to sSubstitute {key} in the content
        file_to_send_full_name: Optional[str]
            full path and name of file to attach to the mail
        file_to_send_type: Optional[str]
            MIME (Multipurpose Internet Mail Extensions) type for the file. See list below, based on the file extension

    Returns: (mgd 2024-06-05)
        » True if the message was or not `Delivered` (the receiving server accepted the message)
            see https://sendgrid.com/en-us/blog/delivered-bounced-blocked-and-deferred-emails-what-does-it-all-mean
          Otherwise, raises an exception

    Raises:
        TypeError: If the provided `send_to_or_dic` is neither a string nor a dictionary.
        ValueError: if the attachment file (file_to_send) has an extension with unknown type.
        RuntimeError: error within the send_mail API
    """
    from ..common.app_context_vars import sidekick

    status_code = 0
    task = ""
    try:

        # Required info: email originator (owner of API_KEY)
        from_email = Email(sidekick.config.EMAIL_ORIGINATOR, sidekick.config.EMAIL_ORIGINATOR_NAME)
        task = "setting email originator"
        if is_str_none_or_empty(from_email.email):
            error = "Unknown `email originator`. Cannot send email."
            raise ValueError(error)

        task = "setting email API key"
        apiKey = sidekick.config.SENDGRID_API_KEY
        if is_str_none_or_empty(apiKey):
            error = "Unknown `email API key`. Cannot send email."
            raise ValueError(error)

        # Get a RecipientsDic from `send_to_or_dic` param
        task = "getting recipients"
        recipients: RecipientsDic = None
        if isinstance(send_to_or_dic, RecipientsListStr):  # RecipientsListStr
            recipients = RecipientsDic(to=send_to_or_dic.as_str)
        elif isinstance(send_to_or_dic, RecipientsDic):
            recipients = send_to_or_dic
        else:
            error = f"Unknown `send_to_or_dic` param's datatype {type(recipients)}, expected is [{RecipientsDic.__name__}|{RecipientsListStr.__name__}]. Cannot send email."
            raise ValueError(error)

        # Attachment type
        task = "getting file extension"
        ext = (
            None
            if is_str_none_or_empty(file_to_send_full_name) or not is_str_none_or_empty(file_to_send_type)
            else path.splitext(file_to_send_full_name)[1].lower()
        )

        task = "checking attachment type"
        if ext is None:
            pass
        elif mime_types.get(ext) is None:
            error = f"Unknown MIME type for extension [{ext}], cannot send email."
            raise ValueError(error)
        else:
            file_to_send_type = mime_types[ext]

        # Body Text
        task = "preparing texts"
        if isinstance(texts_or_section, dict):
            task = "coping texts"
            texts = texts_or_section.copy()
        elif not is_str_none_or_empty(texts_or_section):
            task = "reading texts"
            texts = get_section(texts_or_section)
            for key, value in texts.items():
                if not is_str_none_or_empty(value):
                    try:
                        texts[key] = value.format(**email_body_params)
                    except KeyError as e:
                        sidekick.app_log.error(f"Missing placeholder {e} in params.")
        else:
            error = f"Unknown `texts_or_section` datatype {type(texts_or_section)}, expected is [dict|str]. Cannot send email."
            raise ValueError(error)

        # A nice notice
        if is_str_none_or_empty(recipients.to) and not is_str_none_or_empty(recipients.bcc):
            sidekick.display.warn(
                "Warning: Sending email with only BCC recipient might be rejected by some servers."
            )

        # Create the sendgrid mail
        task = "creating Mail data"
        mail = sendgrid.Mail(
            from_email=from_email,
            subject=texts["subject"],
            html_content=texts["content"],
        )

        # Add recipients (generic way)
        def _addRecipients(
            recipientsStr: RecipientsListStr,
            fAdd: Callable[[str, str], None],
            recipient_class: Type,
        ) -> int:
            result = 0

            for item in recipientsStr.list():
                email, name = recipientsStr.parse(item)
                fAdd(recipient_class(email, name))
                result += 1
            return result

        task = "adding recipients TO"
        _addRecipients(recipients.to, mail.add_to, To)
        task = "adding recipients CC"
        _addRecipients(recipients.cc, mail.add_cc, Cc)
        task = "adding recipients BCC"
        _addRecipients(recipients.bcc, mail.add_bcc, Bcc)

        # Add recipients (generic way)
        task = "preparing Api"
        apiKey = sidekick.config.SENDGRID_API_KEY
        sg = sendgrid.SendGridAPIClient(apiKey)
        if is_str_none_or_empty(file_to_send_full_name):
            pass
        elif not path.exists(file_to_send_full_name):
            raise ValueError(f"File to attach not found [{file_to_send_full_name}].")
        else:
            fileName = path.basename(file_to_send_full_name)
            task = f"reading file [{fileName}]"
            with open(file_to_send_full_name, "rb") as f:
                data = f.read()
            encoded = b64encode(data).decode()
            attachment = sendgrid.Attachment(
                file_content=sendgrid.FileContent(encoded),
                file_type=sendgrid.FileType(file_to_send_type),
                file_name=sendgrid.FileName(fileName),
                disposition=sendgrid.Disposition("attachment"),
            )
            task = f"attaching file [{fileName}]"
            mail.add_attachment(attachment)

        task = f"sending email with subject [{mail.subject}]"
        sidekick.app_log.info(task)

        response = sg.send(mail)
        # https://www.twilio.com/docs/sendgrid/api-reference/how-to-use-the-sendgrid-v3-api/responses#status-codes
        status_code = response.status_code

        sent = status_code in [200, 202]  # api docs says 200, but in practice it's 202
        if not sent:
            raise RuntimeError(f"failed with status code {status_code}")

        return sent
    except Exception as e:
        sc = status_code if status_code != 0 else getattr(e, "status_code", 0)
        error = f"Sendgrid email failed while {task}. Error: [{e}], Status Code: [{sc}]."
        msg = getattr(e, "body", str(e))
        msg_error = f"{error} \nSendGrid: [{msg}]."
        sidekick.app_log.error(msg_error)
        raise RuntimeError(msg_error)


# eof
