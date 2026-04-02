"""
Schema & Seps data import

Reverse the action from scm_export, creating a Dict from the
exported json.

mgd 2025.08
"""

import json
from ..helpers.py_helper import json_to_dict
from ..helpers.types_helper import Usual_Dict


def do_scm_import(json_string: str) -> Usual_Dict:
    """
    Decodes Base64-encoded strings within a dictionary parsed from a JSON string.
    """
    _dict = json.loads(json_string)

    decoded_dict: Usual_Dict = json_to_dict(_dict, True)

    return decoded_dict


# eof
