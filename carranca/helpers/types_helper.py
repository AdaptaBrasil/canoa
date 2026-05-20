"""
This module defines Python Type Aliases to improve code readability and maintainability.

Type Aliases:
- `DBTexts`: A dictionary where both keys and values are strings, typically used for database UI texts.
- `Sep_mgmt_return`: A tuple containing two strings and an integer, used for SEP management return values.
- `CargoItem`: A dictionary representing a JSON-like structure, which may include nested dictionaries.
- `CargoList`: A list of `CargoItem` dictionaries, representing a JSON-like HTML response.
- `TemplateFileFullName`: A string representing the full name of a template file.

Naming Conventions:
Although PEP 613, recommends PascalCase | CapWords (like classes)

variables	 snake_case
functions	 snake_case
classes	     CapWords | PascalCase
type aliases CapWords | PascalCase
constants  	 UPPER_CASE

I do prefer `Pascal_Snake`  ;—)
- Words are Capitalized
- Acronyms are Upper Case
- Words are Separated by underscores
- Acronyms remain readable  (DB_Texts)
- The whole thing stays clean and human-friendly


Author: Equipe da Canoa, 2024

cSpell:ignore
"""

# --- ⚠️ ---
# Avoid adding project-specific imports in this module to prevent circular dependencies.
# Although PEP 613, recommends PascalCase, please use
# `Pascal_Snake`:


from typing import TypeAlias, Protocol, Optional, Any, Dict, Tuple, List, Final
from werkzeug.wrappers import Response as Flask_Response


# Classes
# ----------
# DB_Lookup: TypeAlias = Callable[[str, str], str]
class DB_Lookup(Protocol):
    def __call__(self, key: str, section: str, default_value: str) -> str: ...


# Type Alias
# ----------
Primitive: TypeAlias = str | int | float | bool

""" A dictionary where both keys and values are strings, loaded form the Database ui_items."""
DB_Texts: TypeAlias = Dict[str, str]
DB_Texts_Args: TypeAlias = Tuple | Dict | Primitive | None  #


Usual_Dict: TypeAlias = Dict[str, Any]
JS_Constants: TypeAlias = Dict[str, str]

Sep_Mgmt_Return: TypeAlias = Tuple[str, str, int]

Cargo_Item: TypeAlias = Dict[str, str | Dict[str, str]]
Cargo_List: TypeAlias = List[Cargo_Item]

Template_File_Full_Name: TypeAlias = str
Jinja_Template: TypeAlias = str
Jinja_Rendered: TypeAlias = str


Route_Response: TypeAlias = Jinja_Rendered | Flask_Response

Svg_Content: TypeAlias = str

Opt_List_Of_Str: TypeAlias = Optional[List[str]]

Opt_Str: TypeAlias = Optional[str]

# make str explicit
Error_Message: TypeAlias = str
Success_Message: TypeAlias = str
Json_Text: TypeAlias = str

# Constants
# ---------
NEW_FLASK_RESPONSE: Final[Jinja_Rendered] = ""

# eof
