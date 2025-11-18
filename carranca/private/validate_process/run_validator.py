"""
Fourth step B: Run the validation process

Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024—2025
mgd
"""

# cSpell:ignore

import asyncio

from ..AppUser import AppUser
from ..UserSep import UserSep
from ...common.app_context_vars import sidekick
from ...config.ValidateProcessConfig import DataValidateApp
from ...helpers.py_helper import (
    is_str_none_or_empty,
    decode_std_text,
    quote,
)


async def run_validator(
    batch_full_name: str,
    data_validate_path,
    d_v: DataValidateApp,
    input_folder: str,
    output_folder: str,
    file_name: str,
    app_user: AppUser,
    sep_data: UserSep,
    debug_validator: bool = False,
):
    #  This function knows quite a lot of how to run [data_validate]
    run_command = [
        batch_full_name,
        data_validate_path,  # param 1: path do the data_validate main.py
        d_v.na_in_folder,
        # Named Argumentes:
        input_folder,  # param 2 Don't use " "
        d_v.na_out_folder,
        output_folder,  # param 3   Don't use " "
        d_v.na_user_name,
        quote(app_user.name),  # param 4
        d_v.na_file_name,
        quote(file_name),  # param 5
        d_v.na_schema_se,
        quote(sep_data.fullname),  # param 6
    ]

    if not is_str_none_or_empty(d_v.flags):
        run_command.append(d_v.flags)

    if debug_validator and not is_str_none_or_empty(d_v.flag_debug):
        run_command.append(d_v.flag_debug)
        sidekick.app_log.info(" ".join(run_command))  # LOG
    else:
        sidekick.app_log.debug(" ".join(run_command))  # DEBUG

    # Run the script command asynchronously
    stdout = None
    stderr = None
    exit_code = 0
    try:
        process = await asyncio.create_subprocess_exec(
            *run_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        # Wait for the process to complete
        stdout, stderr = await process.communicate()

        # Get the exit code of the process
        exit_code = process.returncode

    except Exception as e:
        err_msg = f"{d_v.ui_name}.running: {e}, Code [{exit_code}]."
        sidekick.app_log.critical(err_msg)
        return "", err_msg, exit_code

    # Decode the output from bytes to string
    stdout_str = decode_std_text(stdout)
    stderr_str = decode_std_text(stderr)

    return stdout_str, stderr_str, exit_code

# eof
