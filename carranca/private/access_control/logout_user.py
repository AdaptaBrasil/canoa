"""
Tests and confirms that the email and sending functionality
is configured and working correctly.

mgd 2025.10.29 -- 2026.03.20
"""

# cSpell: ignore formdata FlaskForm timestamping


from ...public.ups_handler import get_ups_jHtml
from ...helpers.jinja_helper import Jinja_Rendered, process_template
from ...helpers.route_helper import get_account_response_data, init_response_vars, private_route, is_method_post
from ...common.app_context_vars import app_user
from ...common.app_error_assistant import ModuleErrorCode
from ...helpers.ui_db_texts_manager import UITextsKeys, MSG_DEFAULT


def log_me_out() -> Jinja_Rendered:
    if is_method_post():
        jHtml, _, ui_db_texts, task_code = init_response_vars(ModuleErrorCode.USER_UI_LOGOUT)
        try:
            tmpl_ffn, _, ui_db_texts = get_account_response_data("userUiLogout", "generic_prompt")
            task_code += 1
            ui_db_texts.set_msg_info(MSG_DEFAULT, app_user.name)
            ui_db_texts.set_value(UITextsKeys.Form.width, "")
            ui_db_texts.set_value(UITextsKeys.Form.submit_route, private_route("logout"))
            ui_db_texts.display_msg_only = True
            task_code += 1
            jHtml = process_template(tmpl_ffn, **ui_db_texts.data())

        except Exception as e:
            jHtml = get_ups_jHtml(MSG_DEFAULT, ui_db_texts, task_code, e)

        return jHtml
