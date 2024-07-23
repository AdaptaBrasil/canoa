"""
    Performs the complete validation process:
        1. Check: file name, validates name, create folders
        2. Register: save process info( user, file, & times) in DB.users_files
        3. Unzip unzip the uploaded file
        4. Submit, sends the file to the `data_validate`
        5. Email, data_validate output is sent via email

        Cargo
            is a class to shares: StorageInfo, Params, args, and return values between the 5 modules.

        StorageInfo
            is a class that keep the files & folders names

        Params
            is as class that has the values of Configurable parameters of each module


    Part of Canoa `File Validation` Processes

    Equipe da Canoa -- 2024
    mgd
"""
# cSpell:ignore ext

from ...config_upload import UploadConfig
from ...helpers.py_helper import is_str_none_or_empty, path_remove_last
from ...helpers.user_helper import LoggedUser
from ...helpers.error_helper import ModuleErrorCode
from ..models import UserDataFiles

from .Cargo import Cargo
from .StorageInfo import StorageInfo

from .check import check
from .unzip import unzip
from .register import register
from .submit import submit
from .email import email


def process(
    logged_user: LoggedUser, file_obj: object, valid_ext: list[str]
) -> list[int, str, str]:
    from ...shared import app_config

    current_module_name = __name__.split('.')[-1]

    def __get_next_params(cargo: Cargo) -> list[object, dict]:
        """
        Extracts the parameters of the next procedure,
        initialize cargo and returns to the loop
        """
        params = dict(cargo.next)
        return cargo.init(), params

    def __get_msg_exception(e_str: str, msg_exc: str, code: int) -> str:
        """prepares a complete exception message for the db & log"""
        return f"Upload Error: process.Exception: [{e_str}]; {current_module_name}.Exception: [{msg_exc}], Code [{code}]."

    # Parent folder of both apps: canoa & data_validate
    common_folder = path_remove_last(app_config.ROOT_FOLDER)

    # Create the Storage Info
    storage = StorageInfo(logged_user.code, common_folder)

    # Modules configurable parameters
    upload_cfg = UploadConfig()

    # Create Cargo, with the parameters for the first procedure (check) of the Loop Process
    cargo = Cargo(
        app_config.DEBUG,
        logged_user,
        upload_cfg,
        storage,
        {'file_obj': file_obj, 'valid_ext': valid_ext},  # first module parameters
    )
    error_code = 0
    msg_error = ''
    msg_exception = ''

    """
        Process Loop
        runs all the necessary steps (modules) to generate the final `report` and send it by email.

        `proc` Template:
        def proc(cargo: Cargo, param1, param2, ...) -> cargo:
          ''' process ....
    """
    for current_module in [check, register, unzip, submit, email]:
        current_module_name = current_module.__name__
        try:
            cargo, next_module_params = __get_next_params(cargo)
            error_code, msg_error, msg_exception, cargo = current_module(cargo, **next_module_params)
            if error_code > 0:
                break
        except Exception as e:
            error_code = (
                ModuleErrorCode.UPLOAD_FILE_PROCESS + cargo.step
                if error_code == 0
                else ModuleErrorCode.UPLOAD_FILE_EXCEPTION + error_code
            )
            msg_exception = __get_msg_exception(str(e), msg_exception, error_code)
            break

    current_module_name = 'UserDataFiles.update'
    msg_success = cargo.final.get('msg_success', None)
    if is_str_none_or_empty(cargo.user_data_file__key):
        pass  # user_data_file's pk not ready

    elif error_code == 0:
        try:
            UserDataFiles.update(
                cargo.user_data_file__key,
                error_code=error_code,
                success_text=msg_success,
            )
        except Exception as e:
            log_msg = str(e)
            print(log_msg)

    else:
        try:
            UserDataFiles.update(
                cargo.user_data_file__key,
                error_code=error_code,
                success_text=msg_success, # not really success but standard_output
                error_msg='<sem mensagem de erro>' if is_str_none_or_empty(msg_error) else msg_error,
                error_text=msg_exception,
            )
        except Exception as e:
            error_code = ModuleErrorCode.UPLOAD_FILE_PROCESS + 1
            msg_exception = __get_msg_exception(str(e), msg_exception, error_code)
            print(msg_exception)

    return error_code, msg_error, msg_exception, cargo.final

# eof