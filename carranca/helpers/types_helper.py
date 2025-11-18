"""
This module defines Python Type Aliases to improve code readability and maintainability.

Type Aliases:
- `DBTexts`: A dictionary where both keys and values are strings, typically used for database UI texts.
- `SepMgmtReturn`: A tuple containing two strings and an integer, used for SEP management return values.
- `CargoItem`: A dictionary representing a JSON-like structure, which may include nested dictionaries.
- `CargoList`: A list of `CargoItem` dictionaries, representing a JSON-like HTML response.
- `TemplateFileFullName`: A string representing the full name of a template file.

Naming Conventions:
Type aliases follow `snake_case` naming as per PEP 8 guidelines for better readability and consistency.

Author: Equipe da Canoa, 2024

cSpell:ignore
"""

# --- ⚠️ ---
# Avoid adding project-specific imports in this module to prevent circular dependencies.

from typing import Optional, Any, Dict, Tuple, List

type DBTexts = Dict[str, str]
type UsualDict = Dict[str, Any]
type JsConstants = Dict[str, str]

type SepMgmtReturn = Tuple[str, str, int]

type CargoItem = Dict[str, str | Dict[str, str]]
type CargoList = List[CargoItem]

type TemplateFileFullName = str
type JinjaTemplate = str
type JinjaGeneratedHtml = str

type SvgContent = str

type OptListOfStr = Optional[List[str]]

type OptStr = Optional[str]

# make str type explicit
type ErrorMessage = str
type SuccessMessage = str
type DictAsJson = str
type JsonText = str


# eof
