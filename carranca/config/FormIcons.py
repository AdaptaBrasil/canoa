"""
All Canoa Icons: Forms and Input icons
reference to Font Awesome

mgd 2026.01.06

https://docs.fontawesome.com/web/style/style-cheatsheet
https://docs.fontawesome.com/web/setup/get-started

1. Check if style is available for the plan (free => fas/fa only)
2. Name convention: fas = fa-solid, far = fa-regular, da-light, fa-thin
3. fa-fw centers each icon inside an invisible, making all same width ;—)
4. In canoa.css class color

"""


class FormIconsDict(dict):
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}") from error

    def copy(self) -> "FormIconsDict":
        """Return a cloned FormIconsDict, preserving helper methods."""
        return type(self)(self)

    __copy__ = copy

    def with_icon(self, form_icon: str | None = None) -> "FormIconsDict":
        """Return a clone with a temporary icon value, without mutating the original."""
        clone = self.copy()
        if form_icon and clone.get(form_icon):
            clone["icon"] = clone[form_icon]
        return clone


FormIcons: FormIconsDict = FormIconsDict(
    {
        "style": "fas fa-fw frm-input-icon",  # fa style for all icons
        "icon": "",  # this is a place holder: fi.icon = fi.sep
        # Common
        "name": "fa-location-dot",
        "title": "fa-tag",
        "description": "fa-align-left",
        "text": "fa-file-code",  # text + html
        # validate
        "validate": "fa-file-circle-check",
        "download_file": "fa-file-arrow-down",
        "local_upload": "fa-upload",
        "cloud_upload": "fa-cloud-upload",
        # setor estratégico
        "sep": "fa-puzzle-piece",
        "manager": "fa-circle-user",
        "visible": "fa-eye",
        # schema
        "scm": "fa-vector-square",
        "scm_export": "fa-share-from-square",
        # SPatial Data (file)
        "spd": "fa-layer-group",
        "image": "fa-image",
        "attribute": "fa-user-tag",
        # Documents
        "user_privacy": "fa-user-shield",
        "terms_of_use": "fa-file-shield",
        # User
        "password_change": "fa-user-lock",
        "check_email": "fa-envelope-circle-check",
        "login": "fa-arrow-right-to-bracket",
        "signout": "fa-arrow-right-from-bracket",
        "register": "fa-person-circle-plus",
        "email": "fa-envelope",
        "user": "fa-user",
    }
)


# eof
