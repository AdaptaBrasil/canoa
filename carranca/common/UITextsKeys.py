# mgd
# shortcuts for known UITextsKeys keys


class UITextsKeys:
    ## see carranca\templates\includes\backend-msg.html.j2
    class Msg:
        prompt = "msgPrompt"  # prompt/confirmation text, rendered with no color and no icon
        error = "msgError"
        fatal = "msgFatal"
        info = "msgInfo"
        success = "msgSuccess"
        tech = "msgTech"  # This is an internal type of message, not from db
        warn = "msgWarn"
        # displays only message, no form, inputs/buttons (see .carranca/templates/layouts/form.html.j2 & dialog.html.j2)
        display_msg_only = "msgOnly"

    class Page:
        title = "pageTitle"

    class Form:  # & dialog
        title = "formTitle"
        icon_file = "iconFile"  # only the icon's name
        icon_url = "iconFileUrl"  # url of an png/svg icon dlg_var_icon_url = iconFileUrl, dlg-var-icon-id
        icon_css = ""  # TODO
        user_locale = "userLocale"
        # This button is only visible when msg_only is True OR is a Dialog/Document (see document.html.j2)
        btn_close = "closeFormButton"
        btn_submit = "submitFormButton"
        post_route = "formSubmitRoute"
        size = "dlg_cls_size"

    class Section:
        """
        See table ui_sections.name
        This two sections keys are special (id=1 & id=2):
        as they group all — common —  message
        error and success
        """

        error = "secError"
        success = "secSuccess"
        # only search on the current section
        current = ""  # only search on the current section
        # this is a special key, that has the name of the section
        # loaded in db_Texts, see  get_section
        name = "__section_name__"

    class Fatal:
        no_db_conn = "NoDBConnection"
        code = "UpsErrorCode"
        where = "UpsOffendingDef"
        http_code = "UpsHttpCode"

    class Action:
        dlg_close = "dlgFormCloseAction"
        dlg_goto = "dlgFormGotoAction"
        dlg_sec_msg = "dlgFormSecMsg"


# eof
