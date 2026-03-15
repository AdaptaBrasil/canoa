# mgd
# shortcuts for known UITextsKeys keys


class UITextsKeys:

    class Msg:
        info = "msgInfo"
        warn = "msgWarn"
        error = "msgError"
        success = "msgSuccess"
        fatal = "msgFatal"
        tech = "msgTech"
        # displays only message, no form, inputs/buttons (see .carranca/templates/layouts/form.html.j2 & dialog.html.j2)
        display_msg_only = "msgOnly"

    class Page:
        title = "pageTitle"

    class Form:  # & dialog
        title = "formTitle"
        icon_file = "iconFile"  # only the icon's name
        icon_url = "iconFileUrl"  # url of an png/svg icon dlg_var_icon_url = iconFileUrl, dlg-var-icon-id
        icon_css = ""  # TODO
        date_format = "userDateFormat"
        # This button is only visible when msg_only is True OR is a Dialog/Document (see document.html.j2)
        btn_close = "btnCloseForm"
        submit_route = "fromSubmitRoute"
        pretend_busy = "formSubmitPretendBusy"

    class Fatal:
        no_db_conn = "NoDBConnection"
        code = "UpsErrorCode"
        where = "UpsOffendingDef"
        http_code = "UpsHttpCode"

    class Section:
        """See table ui_sections.nameThis two sections are special (id=1 & id=2):
        as they group all msg error and msgs success"""

        error = "secError"
        success = "secSuccess"
        # this is a special key that has the name of the section loaded in db_Texts,
        # see  get_section
        name = "__section_name__"


# eof
