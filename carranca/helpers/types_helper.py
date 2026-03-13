"""
This module defines Python Type Aliases to improve code readability and maintainability.

Type Aliases:
- `DBTexts`: A dictionary where both keys and values are strings, typically used for database UI texts.
- `Sep_mgmt_return`: A tuple containing two strings and an integer, used for SEP management return values.
- `CargoItem`: A dictionary representing a JSON-like structure, which may include nested dictionaries.
- `CargoList`: A list of `CargoItem` dictionaries, representing a JSON-like HTML response.
- `TemplateFileFullName`: A string representing the full name of a template file.

Naming Conventions:
Type aliases follow `Snake_case` BUT with the first letter uppercase

Author: Equipe da Canoa, 2024

cSpell:ignore
"""

# --- ⚠️ ---
# Avoid adding project-specific imports in this module to prevent circular dependencies.

from typing import TypeAlias, Optional, Any, Dict, Tuple, List, Final
from werkzeug.wrappers import Response as FlaskResponse

# Classes
# ----------

__all__ = ["FlaskResponse"]


# Type Alias
# ----------

Db_texts: TypeAlias = Dict[str, str]
Usual_dict: TypeAlias = Dict[str, Any]
Js_constants: TypeAlias = Dict[str, str]

Sep_mgmt_return: TypeAlias = Tuple[str, str, int]

Cargo_item: TypeAlias = Dict[str, str | Dict[str, str]]
Cargo_list: TypeAlias = List[Cargo_item]

Template_file_full_name: TypeAlias = str
Jinja_template: TypeAlias = str
Jinja_generated_html: TypeAlias = str


Route_response: TypeAlias = Jinja_generated_html | FlaskResponse

Svg_content: TypeAlias = str

Opt_list_of_str: TypeAlias = Optional[List[str]]

Opt_str: TypeAlias = Optional[str]

# make str explicit
Error_message: TypeAlias = str
SuccessMessage: TypeAlias = str
Json_text: TypeAlias = str

# Constants
# ---------
NEW_FLASK_RESPONSE: Final[Jinja_generated_html] = ""

# eof
