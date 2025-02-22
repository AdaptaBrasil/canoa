"""
    Database data retrieve operations helper

    mgd
    Equipe da Canoa -- 2024
"""

# cSpell:ignore psycopg2 sqlalchemy slqaRecords

import json
from datetime import datetime
from typing import Optional, TypeAlias, Union, Tuple, Dict, List, Any
from sqlalchemy import text, Sequence

from carranca import SqlAlchemyScopedSession
from .py_helper import is_str_none_or_empty, to_str

# Array of table's rows as classes -> ListOfDBRecords
ListOfDBRecords: TypeAlias = List["DBRecord"]

JsonStrOfRecords: TypeAlias = str


class DBRecord:
    """
    A class that initializes an instance with attributes from a dictionary.
    """

    name = "db_record"

    def __init__(self, rec_dict: dict, field_types_filter: Optional[List[type]]):
        """
        Args:
            rec_dict (dict): A dictionary containing the attributes to set on the instance.
            field_types_filter (Optional[List[type]]): If provided, only sets attributes that match the types in this list.
            rec_name (Optional[str]): The name of the class. Defaults to None.

        Note:
            If `field_types_filter` is provided, only keys with values matching the specified types will be set as attributes.
        """
        for key, value in rec_dict.items():
            if isinstance(value, field_types_filter) if field_types_filter else True:
                setattr(self, key, value)

    def keys(self):
        return list(self.__dict__.keys())

    def __repr__(self):
        attrs = ", ".join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"<{self.name}({attrs})>"


class DBRecords:
    """
    A class that converts a SQLAlchemy query result into a list of DBRecord instances.
    """

    simple_types_filter: Tuple[type, ...] = (str, int, float, bool, datetime)

    def __init__(
        self,
        table_name: Optional[str] = "",
        slqaRecords: Optional[Sequence] = None,
        filter_types: Optional[Tuple[type, ...]] = None,
        includeNone: bool = True,
    ):
        self.records: ListOfDBRecords = []
        self.table_name = self.__class__.__name__ if is_str_none_or_empty(table_name) else table_name
        self.filter_types = filter_types if filter_types is not None else DBRecords.simple_types_filter
        if includeNone:
            self.filter_types += (type(None),)

        if slqaRecords is not None:
            self.records = [DBRecord(record.__dict__, self.filter_types) for record in slqaRecords]

    def __iter__(self):
        """make DBRecords iterable"""
        return iter(self.records)

    def __len__(self):
        """make DBRecords have len"""
        return len(self.records)

    def __getitem__(self, index):
        """make DBRecords subscriptable"""
        return self.records[index]

    @property
    def count(self):
        return self.__len__()

    def append(self, record_dict: Dict[str, Any]):
        """Appends a new DBRecord object based on the given dictionary."""
        new_record = DBRecord(record_dict, self.filter_types)
        self.records.append(new_record)

    def to_json(self, exclude_fields: Optional[List[str]] = None):
        exclude_fields = (exclude_fields or []) + ["__class__.__name__"]
        return [
            {key: value for key, value in record.__dict__.items() if key not in exclude_fields}
            for record in self.records
        ]

    def __repr__(self):
        attrs = ", ".join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"<{self.table_name}({attrs})>"


def try_get_mgd_msg(error: object, default_msg: str = None) -> str:
    """
    Extracts a custom error message (surrounded by markers)
    from the argument error string, that is typically
    generated by database trigger.

    If not found, the default_msg is returned.

    Example:

    `raise exception '[^|O SEP "%" está atualmente atribuído. Não ...|^]', fullname;`

    """
    start_mgd_marker = "[^|"
    end_mgd_marker = "|^]"
    error_string = to_str(error)
    default_msg = error_string if is_str_none_or_empty(default_msg) else default_msg

    start_index = error_string.find(start_mgd_marker)
    end_index = error_string.find(end_mgd_marker, start_index + len(start_mgd_marker))

    if end_index == -1:
        return default_msg
    else:
        mgd_message = error_string[start_index + len(start_mgd_marker) : end_index]
        is_mgd = len(mgd_message) > 1
        return mgd_message if is_mgd else default_msg


def _execute_sql(query: str):
    """Runs an SQL query and returns the result"""
    result = None
    if not is_str_none_or_empty(query):
        _text = text(query)
        with SqlAlchemyScopedSession() as db_session:
            result = db_session.execute(_text)

    return result


def retrieve_data(query: str) -> Optional[Union[Any, Tuple]]:
    """
    Executes the given SQL query and returns the result in 4 modes:
      1.  N rows c column
      2.  N rows 1 column
      3.  1 row N columns
      4.  1 row 1 column

    Args:
      sql: The SQL query to execute.

    Returns:
      - A tuple of values if the query returns multiple rows with a single column each.
      - A tuple of values if the query returns a single row with multiple columns.
      - A single value if the query returns a single row with a single column.
      - None if an error occurs or the query returns no results.
    """
    from ..common.app_context_vars import sidekick

    try:
        data_rows = _execute_sql(query)
        rows = data_rows.fetchall()

        if not rows:
            return None
        elif len(rows) > 1 and len(rows[0]) > 1:
            # Multiple rows with multiple columns
            return tuple(tuple(row) for row in rows)
        elif len(rows) > 1:
            # Multiple rows with one column each
            return tuple(line[0] for line in rows)
        elif len(rows[0]) > 1:
            # Single row with multiple columns
            return tuple(rows[0])
        else:
            # Single row with a single column
            return rows[0][0]
    except Exception as e:
        sidekick.app_log.error(f"An error occurred retrieving db data [{query}]: {e}")
        return None


def retrieve_dict(query: str):
    """
    Executes the query and attempts to return the result as a dictionary,
    assuming the result consists of two columns (key, value) per row.

    Args:
      query: The SQL query to execute.

    Returns:
      - A dictionary where the first column is the key and the second column is the value.
      - An empty dictionary if the query returns no data or an error occurs.
    """
    from ..common.app_context_vars import sidekick

    data = retrieve_data(query)

    result = {}
    try:
        if data and isinstance(data, tuple):
            # Check if data contains multiple rows of at least two columns
            if all(isinstance(row, tuple) and len(row) >= 2 for row in data):
                result = {row[0]: row[1] for row in data}
            # Handle single row with multiple columns (if returned by retrieve_data)
            elif isinstance(data[0], tuple) and len(data) == 2:
                result = {data[0]: data[1]}
    except Exception as e:
        result = {}
        sidekick.app_log.error(f"An error occurred loading the dict from [{query}]: {e}")

    # # Check if the result is a tuple of tuples (multiple rows)
    # if isinstance(data, tuple) and all(isinstance(row, tuple) and len(row) >= 2 for row in data):
    #     # We expect at least two columns (key, value) for dictionary creation
    #     return {row[0]: row[1] for row in data}

    return result.copy()  # there is a very strange error


def get_str_field_length(table_model: object, field_name: str) -> str:
    """
    Args:
      table_model: Flask SQLAlchemy Table Model
      field_name: the field name (must be string)
    Returns:
      the maximum size defined for the column in the Table Model (*not on the DB*)
    """
    fields = table_model.__table__.columns
    return fields[field_name].type.length


# eof
