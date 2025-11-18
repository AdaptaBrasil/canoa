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
from os import path, stat, access, X_OK

from .Cargo import Cargo
from ...models.private import UserDataFiles
from .run_validator import run_validator
from ...helpers.file_helper import change_file_ext
from ...common.app_context_vars import sidekick
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.py_helper import is_str_none_or_empty, now, OS_IS_LINUX


def _store_report_result(
    ui_name: str,
    stdout_result_pattern: str,
    cargo: Cargo,
    std_out_str: str,
):

    # -------------------------------------
    # Expected <{"data_validate": {"version": "0.5.02", "report": {"errors": 676, "warnings": 609, "tests": 31}}}>

    def _local_result(error: str) -> str:
        error_encoded = json.dumps(error)
        return f'{{"{ui_name}": {{"local_error": "{error_encoded}."}}}}'

    result_json_str = ""
    val_version = "?"
    report_errors = None
    report_warns = None
    report_tests = None
    result = ""
    try:
        if is_str_none_or_empty(stdout_result_pattern):
            result_json_str = _local_result("empty regex pattern")
        elif is_str_none_or_empty(std_out_str):
            result_json_str = _local_result("empty standard output")
        else:
            rd = re.findall(stdout_result_pattern, std_out_str)
            if len(rd) == 0:
                result_json_str = f"{_local_result(f"no data matched regex: [{stdout_result_pattern}]")}\n'std_out_str': [{std_out_str}]"

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
                    sidekick.display.warn(
                        _local_result(f"{len(rd)} data matched. Expected only 1.")
                    )

    except Exception as e:
        result_json_str = _local_result(f"Extraction error [{e}], result [{result}].")

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
            sidekick.app_log.error(
                f"Error saving data_validate result: {result_json_str}: [{e}]."
            )


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
    task_code = 1
    std_out_str = None
    std_err_str = None
    exit_code = 0
    cargo.submit_started_at = now()

    # not run validator test
    # ----------------------
    # return cargo.update(
    #     0,
    #     '',
    #     '',
    #     {"user_report_full_name": 'fake'},
    #     {"msg_success": ''},
    # )

    _path_read = cargo.pd.path.data_tunnel_user_read
    _path_write = cargo.pd.path.data_tunnel_user_write
    try:
        task_code += 1  # 2
        # shortcuts
        _cfg = cargo.receive_file_cfg
        _path = cargo.pd.path

        batch_full_name = _path.batch_full_name
        data_validate_path = cargo.pd.path.data_validate
        batch_has_run_permission = True
        if not path.isfile(batch_full_name):  # TODO send to check module
            task_code += 1  # 3
            raise Exception(
                f"The `{_cfg.dv_app.ui_name}` module caller [{batch_full_name}] was not found."
            )
        elif OS_IS_LINUX and not access(batch_full_name, X_OK):
            batch_has_run_permission = False
            sidekick.display.warn(
                f"Account doesn't have the necessary permissions to execute '{batch_full_name}'."
            )

        result_ext = _cfg.output_file.ext  # ⚠️ keep always the same case (all lower)
        final_report_file_name = f"{_cfg.output_file.name}{result_ext}"
        final_report_full_name = path.join(_path_read, final_report_file_name)
        try:
            task_code = 5  # 5
            std_out_str, std_err_str, exit_code = asyncio.run(
                run_validator(
                    batch_full_name,
                    data_validate_path,
                    _cfg.dv_app,
                    _path_write,
                    _path_read,
                    cargo.pd.received_original_name,
                    cargo.user,
                    cargo.sep_data,
                    cargo.in_debug_mode,
                )
            )
            task_code += 1  # 6
        except Exception as e:
            msg_exception = str(e)
            raise Exception(e)

        # Ok, final report should be waiting for us ;—)

        cargo.report_ready_at = now()

        task_code += 1  # 7
        if not path.exists(final_report_full_name):
            task_code += 1  # 8
            def _x(std_str: str) -> str:
                return f"\n'{std_str}'" if std_str else "'<empty>.'"
            raise Exception(
                f"\n{sidekick.app_name}: Report was not found."
                + (
                    f"\nCheck `x` permission on {batch_full_name}"
                    if not batch_has_run_permission
                    else ""
                )
                + f"\n » {_cfg.dv_app.ui_name}.stderr: {_x(std_err_str)}"
                + f"\n » {_cfg.dv_app.ui_name}.stdout: {_x(std_out_str)}"
                + f"\nExitCode {exit_code}"
                + "\nEnd."
            )
        elif stat(final_report_full_name).st_size < 200:
            task_code += 2  # 9
            raise Exception(
                f"\n{sidekick.app_name}: The report has an invalid size of = {stat(final_report_full_name).st_size}b."
            )
        else:
            # ⚠️ PDF is moved to /canoa/user_files/uploaded/<user_id>
            # copy the final_report file to the same folder and
            # with the same name as the uploaded file,
            # But with extension `result_ext`
            #  (important so later the file can be found):
            user_report_full_name = change_file_ext(
                cargo.pd.working_file_full_name(), result_ext
            )
            task_code += 3  # 10
            shutil.move(final_report_full_name, user_report_full_name)
            task_code += 1  # 11
            error_code = 0 if path.exists(user_report_full_name) else task_code
    except Exception as e:
        error_code = task_code + ModuleErrorCode.RECEIVE_FILE_SUBMIT.value
        msg_exception = str(e)
        sidekick.display.error(msg_exception)
        sidekick.app_log.fatal(msg_exception, exc_info=error_code)
    finally:
        _store_report_result(
            _cfg.dv_app.ui_name,
            _cfg.stdout_result_pattern,
            cargo,
            std_out_str,
        )
        try:
            def _remove_folder(folder: str ):
                msg = f"The intermediate process folder '{folder}' was "
                if path.exists(folder) and path.isdir(folder):
                    shutil.rmtree(folder)
                    sidekick.app_log.info(msg + "removed.")
                else:
                    sidekick.app_log.warning(msg + "not found.")

            if cargo.receive_file_cfg.remove_tmp_files:
                _remove_folder(_path_read)
                _remove_folder(_path_write)
            else:
                sidekick.app_log.info(
                    "The intermediate process folders contents was *not* removed, as requested."
                )
        except e:
            sidekick.app_log.warning(
                f"The intermediate process folders contents were *not* removed because of an error [{e}]."
            )

    # goto email.py
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
