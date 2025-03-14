"""
Fourth step: Submit to validation

Part of Canoa `File Validation` Processes

Equipe da Canoa -- 2024—2025
mgd
"""

# cSpell:ignore nobuild

import re
import json
import shutil
import asyncio
from os import path, stat

from .Cargo import Cargo
from ..models import UserDataFiles
from ..LoggedUser import LoggedUser
from ...helpers.py_helper import to_int
from ...helpers.file_helper import change_file_ext
from ...helpers.error_helper import ModuleErrorCode
from ...common.app_context_vars import sidekick
from ...config.config_validate_process import DataValidateApp
from ...helpers.py_helper import (
    is_str_none_or_empty,
    decode_std_text,
    quote,
    now,
)


async def _run_validator(
    batch_full_name: str,
    data_validate_path,
    d_v: DataValidateApp,
    input_folder: str,
    output_folder: str,
    file_name: str,
    user: LoggedUser,
    debug_validator: bool = False,
):
    #  This function knows quite a lot of how to run [data_validate]

    sep_full_name = "[Nenhum]" if user.sep is None else user.sep.full_name

    run_command = [
        batch_full_name,
        data_validate_path,  # param 1: path do the data_validate main.py
        d_v.na_in_folder,
        # Named Argumentes:
        input_folder,  # param 2 Don't use " "
        d_v.na_out_folder,
        output_folder,  # param 3   Don't use " "
        d_v.na_user_name,
        quote(user.name),  # param 4
        d_v.na_file_name,
        quote(file_name),  # param 5
        d_v.na_schema_se,
        quote(sep_full_name),  # param 6
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


def _store_report_result(
    ui_name: str,
    stdout_result_pattern: str,
    cargo: Cargo,
    std_out_str: str,
):

    # -------------------------------------
    # Expected <{'data_validate': {'version': '0.5.02', 'report': {'errors': 676, 'warnings': 609, 'tests': 31}}}>

    def _local_result(error: str) -> str:
        error_encoded = json.dumps(error)
        return f'{{"{ui_name}": {{"local_error": "{error_encoded}."}}}}'

    result_json_str = ""
    val_version = "?"
    report_errors = None
    report_warns = None
    report_tests = None
    try:
        if is_str_none_or_empty(stdout_result_pattern):
            result_json_str = _local_result("empty regex pattern")
        elif is_str_none_or_empty(std_out_str):
            result_json_str = _local_result("empty standard output")
        else:
            rd = re.findall(stdout_result_pattern, std_out_str)
            if len(rd) == 0:
                result_json_str = _local_result(f'no data matched "{stdout_result_pattern}"')
            else:
                result_json_str = rd[0][1:-1]
                result = ""
                try:
                    result = json.loads(result_json_str)
                except:
                    result_json_str = result_json_str.replace("'", '"')
                    result = json.loads(result_json_str)

                val_version = result["data_validate"]["version"]
                report = result["data_validate"]["report"]
                report_errors = report["errors"]
                report_warns = report["warnings"]
                report_tests = report["tests"]
                if len(rd) > 1:
                    sidekick.display.warn(_local_result(f"{len(rd)} data matched. Expected only 1."))

    except Exception as e:
        result_json_str = _local_result(f"Extraction error [{e}]")

    finally:
        try:
            UserDataFiles.update(
                cargo.table_udf_key,
                e_unzip_started_at=cargo.unzip_started_at,
                f_submit_started_at=cargo.submit_started_at,
                g_report_ready_at=cargo.report_ready_at,
                # local info
                validator_version=val_version,
                validator_result=result_json_str,
                report_errors=report_errors,
                report_warns=report_warns,
                report_tests=report_tests,
            )
        except Exception as e:
            sidekick.app_log.error(f"Error saving data_validate result: {result_json_str}: [{e}].")


def submit(cargo: Cargo) -> Cargo:
    """
    Submit the unzip files to app `data_validate` and
    wait for the report

    This function knows all about this app [carranca]
        and nothing about data_validate app
        except the parameters needed to call 'main.py'
    """

    user_report_full_name = "<not produced>"
    msg_error = "receiveFileSubmit_error"
    error_code = 0
    msg_exception = ""
    task_code = 0
    std_out_str = None
    std_err_str = None
    exit_code = 0
    cargo.submit_started_at = now()

    # return cargo.update(
    #     0,
    #     '',
    #     '',
    #     {"user_report_full_name": 'fake'},
    #     {"msg_success": ''},
    # )

    try:
        task_code += 1  # 1
        # shortcuts
        _cfg = cargo.receive_file_cfg
        _path = cargo.pd.path
        _path_read = cargo.pd.path.data_tunnel_user_read
        _path_write = cargo.pd.path.data_tunnel_user_write
        batch_full_name = _path.batch_full_name
        data_validate_path = cargo.pd.path.data_validate
        if not path.isfile(batch_full_name):  # TODO send to check module
            task_code += 1  # 2
            raise Exception(f"The `{_cfg.dv_app.ui_name}` module caller [{batch_full_name}] was not found.")

        result_ext = _cfg.output_file.ext  # /!\ keep always the same case (all lower)
        final_report_file_name = f"{_cfg.output_file.name}{result_ext}"
        final_report_full_name = path.join(_path_read, final_report_file_name)

        try:
            task_code += 2  # 3
            std_out_str, std_err_str, exit_code = asyncio.run(
                _run_validator(
                    batch_full_name,
                    data_validate_path,
                    _cfg.dv_app,
                    _path_write,
                    _path_read,
                    cargo.pd.received_original_name,
                    cargo.user,
                    cargo.in_debug_mode,
                )
            )
            task_code += 1  # 4
        except Exception as e:
            msg_exception = str(e)
            raise Exception(e)

        # Ok, final report should be waiting for us ;—)

        cargo.report_ready_at = now()

        task_code += 1  # 5
        if not path.exists(final_report_full_name):
            task_code += 1  # 6
            raise Exception(
                f"\n{sidekick.app_name}: Report was not found.\n » {_cfg.dv_app.ui_name}.stderr:\n{std_err_str}\n » {_cfg.dv_app.ui_name}.stdout:\n {std_out_str}\n ExitCode {exit_code}\n » End."
            )
        elif stat(final_report_full_name).st_size < 200:
            task_code += 2  # 7
            error_code = task_code
        else:
            # copy the final_report file to the same folder and
            # with the same name as the uploaded file,
            # But with extension `result_ext`
            #  (important so later the file can be found):
            user_report_full_name = change_file_ext(cargo.pd.working_file_full_name(), result_ext)
            task_code += 3  # 8
            shutil.move(final_report_full_name, user_report_full_name)
            task_code += 1  # 9
            error_code = 0 if path.exists(user_report_full_name) else task_code
    except Exception as e:
        error_code = task_code
        msg_exception = str(e)
        sidekick.app_log.fatal(msg_exception, exc_info=error_code)
    finally:
        _store_report_result(
            _cfg.dv_app.ui_name,
            _cfg.stdout_result_pattern,
            cargo,
            std_out_str,
        )
        try:
            if cargo.receive_file_cfg.remove_tmp_files:
                shutil.rmtree(_path_read)
                shutil.rmtree(_path_write)
            else:
                pass  # rename and move?

        except:
            sidekick.app_log.warning("The communication folders between apps were *not* deleted.")

    # goto email.py
    error_code = 0 if (error_code == 0) else error_code + ModuleErrorCode.RECEIVE_FILE_SUBMIT
    if error_code == 0:
        sidekick.display.info(
            f"submit: The unzipped files were submitted to '{_cfg.dv_app.ui_name}' and a report was generated."
        )
    else:
        sidekick.app_log.error(
            f"There was a problem submitting the files to '{_cfg.dv_app.ui_name}'. Error code [{error_code}] and Exit code [{exit_code}]."
        )

    return cargo.update(
        error_code,
        msg_error,
        msg_exception,
        {"user_report_full_name": user_report_full_name},
        {"msg_success": std_out_str},
    )


# eof
