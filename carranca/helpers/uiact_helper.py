"""

ui-action-response <-> py communication infrastructure

mgd

"""

# cSpell:words nsert

import json
from typing import Optional, Tuple, Any, Dict

from ..helpers.py_helper import to_int
from ..helpers.types_helper import UsualDict, JsonText
from ..common.app_error_assistant import AppStumbled

DATA_SEPARATOR = ":"

class UiActResponseKeys:
    # Defines the response's ui commands actions keys of `sep_grid` `scm_grid`, scm_e etc
    action = "act"
    code = "code"
    row_index = "idx"
    grid = "grd"
    data = "data"
    # request actions:
    unknown = "?"
    edit = "E"
    insert = "I"
    delete = "D"
    save = "S"
    export = "X"


class UiActResponse:
    action: str = ""
    code: str = ""
    row_index = 0
    data: Dict[str, Any]

    def _get_value(self, key: str) -> str:
        value = self.data[key] if key in self.data else "?"
        return value

    def __init__(self, cmd_text_or_code: str | JsonText):
        try:
            ## is 'cmd_text_or_code' is json?
            self.data = json.loads(cmd_text_or_code)
            self.action = self._get_value(UiActResponseKeys.action)[0]
            self.code = self._get_value(UiActResponseKeys.code)
            self.row_index = to_int(self._get_value(UiActResponseKeys.row_index))
        except:
            ## No, 'cmd_text_or_code' is not json, so is s code
            if (code:= cmd_text_or_code.strip()) in [UiActResponseProxy.add, UiActResponseProxy.null, UiActResponseProxy.show]:
                # TODO: code => cmd
                self.code = code
            else:
                raise AppStumbled(f'Unknown UI Action Response <code>{code}</code>.')

    def initial(self) -> UsualDict:
        return {
            "action": '',
            "row_index": self.row_index,
            "code": '',
            "data": None,
        }

    def encode(self) -> str:
        data = UiActResponseProxy().encode(self.action, self.code, self.row_index)
        return data


class UiActResponseProxy:
    # Send response from UI
    add = "!++"
    null = "!~~"
    show = "!##"

    def has_data(self, data: str) -> bool:
        # action:code
        return DATA_SEPARATOR in data

    def encode(self, action: str, code: str, row_index=0) -> str:
        data = f"{action}{DATA_SEPARATOR}{code}{DATA_SEPARATOR}{row_index}"
        return data

    def decode(self, data: str) -> Tuple[Optional[str], str, Optional[int]]:
        if not self.has_data(data):
            code = data
            return None, code, None

        """
        action:code:row_index
        -----------
        `action` can be:
            » None: is a call from the menu, no action.
              After edit or insert, return to standard login()
                or
            » [C]reate, [I]nsert, [E]dit
            It is the first char of the button that trigger the action in
                `private/sep_grid.html.j2`
            and routed here via
                `private/rout("/sep_grid/<code>")`
            See sep_grid.html.j2  { -- Action Triggers -- }
            After edit or insert, return to the calling grid & select this row
        """
        action = data.split(DATA_SEPARATOR)[0]

        """
        `code` can be:
            » GridAction.add : insert a new SEP
              or
            » The obfuscate ID of the SEP to edit
              or
            ...
        """
        code = data.split(DATA_SEPARATOR)[1]

        """
        `row_index` is the selected row index of a grid, selected again on return
        # TODO, now optional
        """
        row_index = to_int(f"{data}{DATA_SEPARATOR}".split(DATA_SEPARATOR)[2], 0)

        return action, code, row_index


# eof
