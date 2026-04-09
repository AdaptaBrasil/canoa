"""
Data Types
----------
Database data retrieve & operations for SQLAlchemy

mgd
Equipe da Canoa --  2024 — 2025
"""

# cspell:ignore SQLA

from typing import TypeAlias, Dict, List, Any
from datetime import datetime

Json_Str_Of_Records: TypeAlias = str

DBRecord_Data: TypeAlias = Dict[str, str | int | float | bool | datetime]


# see  declarative_base
# https://stackoverflow.com/questions/45259764/how-to-create-a-single-table-using-sqlalchemy-declarative-base
# see ...private.models Base = declarative_base()

SQLA_Base_Table: TypeAlias = Any  # reduce to types

SQLA_Statement: TypeAlias = Any  # reduce to types

SQLA_Base_Records: TypeAlias = List[Any]  # improve
# eof
