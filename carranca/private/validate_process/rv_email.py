"""
Revalidation, sixth and final step:
    Send an email with the validation report attached:
        - SEP has a manager: to manager, cc adm (`report_email_cc`, as email.py)
        - SEP has no manager: to adm, no cc
        - no manager & no adm: to the user who started the revalidation

    Mirrors email.py, which hard-codes recipients & texts section.

Part of Canoa `File Validation` Processes (Revalidation)

Equipe da Canoa -- 09.2026
mgd
"""

from .Cargo import Next_Cargo, Cargo
from ...models.private.user_data_files import UserDataFiles
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.py_helper import is_str_none_or_empty, now_as_text, now
from ...helpers.email_helper import RecipientsDic, RecipientsList, send_email

# TODO 2026-09-16 create DB texts section "revalidatedFile_email" ("the validator was updated, check the new results")
RV_EMAIL_TEXTS = "uploadedFile_email"


def rv_email(cargo: Cargo, user_report_full_name: str, report_recipient: object | None) -> Next_Cargo:
    """`report_recipient`: the SEP's current manager (name, email) or None"""
    proc = "[rv_email]: "
    msg_exception = ""
    task_code = 0
    try:
        cargo.email_started_at = now()
        task_code += 1  # 1
        adm_cc = cargo.receive_file_cfg.report_email_cc
        if report_recipient is not None:
            greet_name = report_recipient.name
            recipients = RecipientsDic(to=RecipientsList(report_recipient.email, report_recipient.name), cc=adm_cc)
        elif not is_str_none_or_empty(adm_cc):
            greet_name = cargo.user.name
            recipients = RecipientsDic(to=adm_cc)
        else:
            greet_name = cargo.user.name
            recipients = RecipientsDic(to=RecipientsList(cargo.user.email, cargo.user.name))
            sidekick.display.warn(f"{proc}No manager and no adm cc: the report goes to {cargo.user.name}.")

        email_body_params = {
            "user": greet_name,
            "receipt": cargo.pd.user_receipt,
            "when": now_as_text(),
        }

        task_code += 1  # 2
        send_email(recipients, RV_EMAIL_TEXTS, email_body_params, user_report_full_name)
        sidekick.display.info(f"{proc}An email was sent to [{recipients.to}] with the result of the revalidation.")

        task_code += 2  # 4
        UserDataFiles.update(
            cargo.table_udf_key,
            h_email_started_at=cargo.email_started_at,
            email_sent=True,
        )
        sidekick.display.info(f"{proc}The revalidation process DB record was updated with the email info.")
        task_code = 0  # !important
    except Exception as e:
        task_code += 5
        msg_exception = str(e)
        sidekick.display.fatal(f"{proc}There was a problem sending the results email: {msg_exception}.")

    error_code = 0 if task_code == 0 else ModuleErrorCode.RECEIVE_FILE_EMAIL.value + task_code
    return cargo.update(error_code, "uploadFileEmail_failed", msg_exception)


# eof
