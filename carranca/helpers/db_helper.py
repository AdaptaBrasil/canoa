"""
Database data retrieve operations helper

mgd
Equipe da Canoa -- 2024
"""

# cSpell:ignore sqlalchemy slqaRecords connstr

from typing import Optional, TypeAlias, Union, Tuple, Dict, List, Any, Callable
from datetime import datetime
from sqlalchemy import text, Sequence
from sqlalchemy.orm import Session
from sqlalchemy.exc import DatabaseError, OperationalError, ProgrammingError
from sqlalchemy.engine import CursorResult

# from psycopg2.errors import ProgrammingError as psycopg2_ProgrammingError

from .py_helper import is_str_none_or_empty, to_str
from .types_helper import ui_db_texts

from .. import global_sqlalchemy_scoped_session
from ..config import BaseConfig
from ..common.app_context_vars import sidekick
from ..common.app_error_assistant import AppStumbled, ModuleErrorCode

# Array of table's rows as classes -> ListOfDBRecords
ListOfDBRecords: TypeAlias = List["DBRecord"]

JsonStrOfRecords: TypeAlias = str


def db_connstr_obfuscate(config: BaseConfig):
    """Hide any confidential info before it is displayed in debug mode"""
    import re

    db_uri_safe = re.sub(
        config.SQLALCHEMY_DATABASE_URI_REMOVE_PW_REGEX,
        config.SQLALCHEMY_DATABASE_URI_REPLACE_PW_STR,
        config.SQLALCHEMY_DATABASE_URI,
    )
    config.SQLALCHEMY_DATABASE_URI = db_uri_safe
    config.SQLALCHEMY_DATABASE_URI_REMOVE_PW_REGEX = ""
    config.SQLALCHEMY_DATABASE_URI_REPLACE_PW_STR = ""
    config.SQLALCHEMY_DATABASE_URI = ""

    return


class DBRecord:
    """
    A class that initializes an instance with attributes from a dictionary.
    """

    # name = "db_record" use  return self.__class__.__name__

    def __init__(
        self,
        rec_dict: Dict[str, Any],
        field_names_filter: Optional[List[str]] = None,
        field_types_filter: Optional[List[type]] = None,
    ):
        """
        Args:
            rec_dict (dict): A dictionary containing the attributes to set on the instance.
            field_names_filter (Optional[List[str]]): If provided, only sets attributes whose names are in this list
                and return the keys in that order.
            field_types_filter (Optional[List[type]]): If provided, only sets attributes that match the types in this list.

        Note:
            If `field_names_filter` is provided, only keys with names in the list will be set as attributes.
            If `field_types_filter` is provided, only keys with values matching the specified types will be set as attributes.
        """
        if field_names_filter is None:
            key_values = list(rec_dict.items())
        else:
            key_values: List[tuple[str, Any]] = []
            for field in field_names_filter:
                if field in rec_dict:
                    key_values.append((field, rec_dict[field]))

        for key, value in key_values:
            if isinstance(value, field_types_filter) if field_types_filter else True:
                setattr(self, key, value)

    def keys(self):
        return list(self.__dict__.keys())

    def __getitem__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        raise KeyError(f"'{key}'")

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
        field_names_filter: Optional[List[str]] = None,
        filter_types: Optional[Tuple[type, ...]] = None,
        includeNone: bool = True,
    ):
        self.records: ListOfDBRecords = []
        self.table_name = self.__class__.__name__ if is_str_none_or_empty(table_name) else table_name
        self.field_names_filter = (
            field_names_filter
            if isinstance(field_names_filter, List) and len(field_names_filter) > 0
            else None
        )
        self.filter_types = filter_types if filter_types is not None else DBRecords.simple_types_filter

        if includeNone:
            self.filter_types += (type(None),)

        if slqaRecords is not None:
            self.records = [
                DBRecord(record.__dict__, self.field_names_filter, self.filter_types)
                for record in slqaRecords
            ]

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
    def count(self) -> int:
        return self.__len__()

    def append(self, record_dict: Dict[str, Any]) -> None:
        """Appends a new DBRecord object based on the given dictionary."""
        new_record = DBRecord(record_dict, self.field_names_filter, self.filter_types)
        self.records.append(new_record)

    def to_json(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        exclude_fields = (exclude_fields or []) + ["__class__.__name__"]
        return [
            {key: value for key, value in record.__dict__.items() if key not in exclude_fields}
            for record in self.records
        ]

    def keys(self):
        return self.records[0].keys() if len(self.records) > 0 else []

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


def db_fetch_rows(
    func_or_query: str | Callable[[Session, Any], Any], return_tuple_len: int = 1, *args, **kwargs
) -> Tuple[Optional[Exception], Optional[str], Tuple[Any, ...] | CursorResult]:
    """
    Executes a SQL query or a function within a database session.

    Args:
        func_or_query: A callable function or a SQL query string.
        *args: Additional positional arguments to pass to the function.
        **kwargs: Additional keyword arguments to pass to the function.

    Returns:
        A tuple containing:
            - An error (if any)
            - A message
            - Returns, if type of func_or_query is
                callable: A tuple of unknown size
                str: CursorResult

        A tuple containing an error (if any) and the result of the query or function.

    """

    def _do_return_error(e: Exception, msg: str) -> Tuple[Exception, str, Tuple]:
        from ..common.app_context_vars import sidekick

        # TODO LOG to log
        err_code = f"[{e.code}]" if hasattr(e, "code") else ""
        sidekick.display.error(f"[{func_or_query}]: '{msg}': Error{err_code} details: {e}.")
        return e, msg, tuple([None] * return_tuple_len)

    try:
        db_session: Session
        with global_sqlalchemy_scoped_session() as db_session:
            if callable(func_or_query):
                returned = func_or_query(db_session, *args, **kwargs)
                return None, None, returned
            elif isinstance(func_or_query, str):
                query = text(func_or_query)
                cursor: CursorResult = db_session.execute(query)
                return None, None, cursor
            else:
                return _do_return_error(
                    TypeError(f"Invalid argument type in {__name__}"),
                    f"[{func_or_query}]: is not callable nor str.",
                )
    # https://docs.sqlalchemy.org/en/13/errors.html
    # https://docs.sqlalchemy.org/en/13/errors.html#programmingerror
    except ProgrammingError as e:
        return _do_return_error(e, "Evaluating the SQL request.")

    # https://docs.sqlalchemy.org/en/13/errors.html#operationalerror
    except (OperationalError, DatabaseError) as e:
        return _do_return_error(e, "Database connection error.")

    except Exception as e:
        return _do_return_error(e, "Error executing SQL.")


def retrieve_rows(query: str) -> Optional[Union[Any, Tuple]]:
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
        err, _, data_cursor = db_fetch_rows(query)
        # TODO:
        if err:
            raise err

        rows = data_cursor.fetchall() if data_cursor else None

        if not rows:
            return tuple()
        elif len(rows) > 1 and len(rows[0]) > 1:
            # Multiple rows with multiple columns
            return tuple(tuple(row) for row in rows)
        elif len(rows) > 1:
            # Multiple rows with one column
            return tuple(line[0] for line in rows)
        elif len(rows[0]) > 1:
            # Single row with multiple columns
            return tuple(rows[0])
        else:
            # Single row with a single column
            return (rows[0][0],)
    except Exception as e:
        sidekick.app_log.error(f"An error occurred retrieving db data [{query}]: {e}")
        return tuple()


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

    data = retrieve_rows(query)

    result: ui_db_texts = {}
    try:
        if data and isinstance(data, tuple):
            # Check if data contains multiple rows of at least two columns
            if all(isinstance(row, tuple) and len(row) >= 2 for row in data):
                result = {row[0]: row[1] for row in data}
            # Handle single row with multiple columns (if returned by retrieve_rows)
            elif len(data) > 1 and not isinstance(data[0], tuple):
                # result = {data[0]: data[1]}
                result = {data[i]: data[i + 1] for i in range(0, len(data) - 1, 2)}
    except Exception as e:
        sidekick.app_log.error(f"An error occurred loading the dict from [{query}]: {e}")
        result = {}

    # # Check if the result is a tuple of tuples (multiple rows)
    # if isinstance(data, tuple) and all(isinstance(row, tuple) and len(row) >= 2 for row in data):
    #     # We expect at least two columns (key, value) for dictionary creation
    #     return {row[0]: row[1] for row in data}

    return result.copy()  # there is a very strange error


def get_str_field_length(table_model: object, field_name: str) -> int:
    """
    Args:
      table_model: Flask SQLAlchemy Table Model
      field_name: the field name (must be string)
    Returns:
      the maximum size defined for the column in the Table Model (*not on the DB*)
    """
    fields = table_model.__table__.columns
    return fields[field_name].type.length


# TODO
def db_ups_error(e: Exception, msg_error: str, table_name: str) -> None:
    if not e is None:
        sidekick.display.error(f"Fatal error while fetching rows in table [{table_name}]: {msg_error}")
        raise AppStumbled(msg_error, ModuleErrorCode.DB_FETCH_ROWS, False, True)

    return


# eof
