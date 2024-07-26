<!--
   /* cSpell:locale en
   /* cSpell:ignore docstrings pythonic hexdigest hashlib urandom lucuma
-->

# Documenting Python Code
>   _Annotated by Miguel Gastelumendi with the help of Gemini_
>   Last update 2024-06-22


## Introduction
This guide provides an overview of effective practices for documenting Python code. Well-documented code is easier to understand, maintain, and reuse, leading to a smoother development experience.

### Benefits of Documentation

* **Improved Maintainability** Clear documentation makes it easier to understand code logic and modify it later, even by someone unfamiliar with the codebase.
* **Enhanced Readability** Well-documented code is clearer to read and follow, reducing debugging time and confusion.
* **Effective Collaboration** Shared documentation facilitates team communication and allows others to contribute effectively.

### Documentation Styles

There are several ways to document Python code, each with its purpose


* **Hints**
    Type hints provide optional type annotations using the `typing` module. These annotations clarify the expected data types for variables, function arguments, and return values.

    The enhanced static type checking offered by Hints allows tools such as `mypy` or `pyright` to detect possible type-related errors at the time of development.

    > _Hints_ are used along the code: (see below [Data Types](#data-types) for more example)
    ```python
    from typing import Dict

    class BaseConfig:
        """
        The Base Configuration Class for the App
        """
        #etc

    app_mode_production : str = 'Production'
    app_mode_debug = 'Debug'

    # Load all possible configurations
    config_modes: Dict[str, BaseConfig] = {
        app_mode_production: ProductionConfig(),
        app_mode_debug     : DebugConfig()
    }

    ```

* **Docstrings**
    Built-in comments within functions, classes, and modules that provide concise explanations of their purpose, parameters, and return values.

    > _Docstrings_ are marked with triple double quotes (`"""`) or three backticks (`` ``` ``) at the beginning and end.

    ```python
    class MyClass:
        """
        This is the docstring for the MyClass class.
        """
        #etc

        def my_method(self):
            """
            This is the docstring for the my_method function.
            """
            #etc

    # Accessing class docstring, with __doc__ or help()
    class_doc = MyClass.__doc__
    help(MyClass)
    method_doc = MyClass().my_method.__doc__
    ```
* **Comments** Inline comments within code blocks to clarify specific logic or non-obvious sections.
    > _Comments_ are started with a hash symbol `#` any where in the line.
* **External Documentation** Separate files (like READMEs or markdown files) to provide more detailed explanations, examples, and usage instructions.

### Docstring Guidelines (PEP 257)

PEP 257 outlines conventions for writing clear and informative docstrings. Here's a breakdown of its structure:

1. **Short Summary** A one-line description of the function/class/module's purpose.
2. **Blank Line** Separates the summary from the detailed explanation.
3. **Detailed Description** A multi-line explanation of the function's functionality, including:
    * `Args:` Explain each parameter name, type, and default value (if any).
    * `Returns:` Describe the value returned by the function and its type.
    * `Raises:` List any exceptions raised by the function and their meanings.


```python
# Here's an example of a well-structured docstring following PEP 257:
def calculate_area(length: float, width: float) -> float:
  """Calculates the area of a rectangle.

  Args:
      length (float): The length of the rectangle.
      width (float): The width of the rectangle.

  Raises:
      ValueError: If either length or width is negative.

  Returns:
      float: The area of the rectangle (length * width).
  """
  if length < 0 or width < 0:
    raise ValueError("Length and width must be non-negative.")

  return length * width
```

## Data Types

Python offers various built-in data types for storing and organizing information. These data types are essential for structuring your code effectively and making it more readable. Here's a list of commonly used single and collection data types you might encounter in Python:

**Single**

* **`int`** _(integer)_ Represents whole numbers
    ```python
    age: int= 10
    temp: int= -5
    ```
* **`float`** _(floating-point)_ Represents numbers with decimals
    ```python
    pi: float = 3.14159
    x: float = -2.5e2
    ```

* **`str`** _(string)_ Represents textual data enclosed in quotes
    ```python
    user_name: str = request.form.get(name)
    target: str = 'Pythonic'
    ```
* **`bool`** _(boolean)_ Represents logical values, either `True` or `False`.
    ```python
    remember_me: bool = not is_str_none_or_empty(request.form.get('remember_me'))
    ```
* **`None`** _( )_  Indicates the absence of a value.

**Collection**
> If the collection has elements  of more than one type use Union[] or Sequence, avoid using `Any` type (because is a poor description). Below, _ordered_ and _unordered_ refers to the access method to the items, not to the lexical order of the elements.
* **`list`** Ordered sequence of mutable elements, allowing duplicates (general purpose, dynamic collections)
    > Offers: append(x), count(x), index(x), insert(i, x), pop(i), remove(x), reverse(), sort()
    ```python
    from typing import List, Sequence

    fruits: List[str] = ['apple', 'lucuma', 'banana', 'cherry', 'lucuma']
    fruits.sort()
    data: Sequence = ['apple', 3, True]
    ```
* **`tuple`** Ordered sequence of immutable unique elements (fixed data, function arguments, dic keys)
    > Offers: count(x), index(x)
    ```python
    from typing import Tuple, Union

    bh_coordinates: Tuple[float, float] = (-19.912998, -43.940933)
    send: tuple[Union[bool, int, str]] = (10, 'hello', True, 34, 903, 23)
    ```
* **`set`** Unordered collection of unique mutable elements
    > Offers: add(x), difference(set), discard(x), in, intersection(set), pop(), remove(x), union(set)

    ```python
    from typing import Set

    my_set: Set[int] = {1, 2, 5, 12, 3}
    u_words: Set[str] = set('A set of non unique words to find unique words'.lower().split())
    ```
* **`dict` (dictionary)** Unordered collection of key&lt;immutable+hashable>-value&lt;any> pairs
    > Offers: get(key, default), items(), keys(), pop(key, default), update(other_dict), values()
    ```python
    email_to = {'to': user.email, 'cc': user.chief.email}
    ```

**Functions**
    Callable


## Naming Conventions

Choosing clear and descriptive names is an essential aspect of writing readable and maintainable code.

**snake_case**
* Most widely used convention for *variables*, attributes and *functions* names.
* Uses lowercase letters separated by underscores (`_`).
* Examples: `first_name`, `total_sales`, `is_active`.

**__sleeping_snake_case**
* By convention, members with names starting with double underscores (`__`) are considered private, and signal to discourage direct user access.
 See below [Public vs. Private Members](#public-vs.-private-members).
* Uses a snake_case name that starts with double underscores (`__`).
* The name `__sleeping_snake_case` is a creation of mine.
* Examples: `__init__`, `__seed_number`

**PascalCase**
* Preferred convention for *classes*.
* Uses first letter of each word uppercase (including the first word, unlike `camelCase`).
* Examples: `ClassName`, `EmailAddress`, `Customer`.

**UPPERCASE_SNAKE_CASE**
* Typically used for *constants* and *enums*.
* All uppercase letters separated by underscores.
* Examples: `MAX_SPEED`, `PI`, `DEBUG_MODE`.

**Package and Module Names**
* Typically use snake_case for packages and modules as well.

**PEP 8 Style Guide**
* The official Python style guide (https://peps.python.org/pep-0008/) offers additional recommendations on variable naming and other coding conventions.


## Public vs. Private Members

In object-oriented programming, managing member visibility is crucial for code organization and maintainability. Python offers conventions to achieve encapsulation. But it doesn't have strict privacy enforcement like some other languages.

* **Public Members** Members without any special naming conventions are considered public. They can be accessed directly from anywhere in your code, outside the class definition as well.

* **Private Members** *(by Convention, not enforced)* Members with names starting with double underscores (__) are considered private. This is a convention to discourage direct access from outside the class, but not enforced by the language.

  However, technically, these members can still be accessed from outside the class if someone bypasses [encapsulation](#encapsulation) principles.


### Encapsulation
Python relies on encapsulation principles to discourage direct access to internal implementation details. This promotes better code organization and maintainability.

Here are common practices to achieve this:

* **Private Attribute and Methods**  Use name methods with double underscores to indicate they're intended for internal use within the class.

* **Getter/Setter Methods** If you want controlled access to an attribute, create public methods (without double underscores) to get or set its value. This allows you to manage the access logic within these methods.

```python
#RandomSHA256.py
import hashlib
import os

class RandomSHA256:
  """
  Generates random SHA256 hash strings using a combination of seed and randomness.

  Attributes:
      __seed (int): A private constant used as part of the seeding process.
  """

  def __init__(self, seed: int):
    """
    Initializes a RandomSHA256 object with a private seed constant.

    Args:
        seed (int): An integer value used as part of the seeding process.
    """
    # --- Private attribute, starts with double underscore ---
    self.__seed = seed

  # --- Public readonly access to the private member ---
  @property
  def seed(self) -> int:
    """ This getter method provides controlled access to the `private` __seed attribute."""
    return self.__seed

  def generate(self) -> str:
    """Generates a random SHA256 hash string.

    Returns:
        str: A hexadecimal string representing the SHA256 hash.
    """
    h = hashlib.sha256()

    # Combine seed with random bytes for better randomness
    h.update(str(self.__seed).encode() + os.urandom(10))  # Add 10 random bytes
    return h.hexdigest()
```
```python
#test_of_RandomSHA256.py
from RandomSHA256 import RandomSHA256

    random_sha256 = RandomSHA256(12345)
    print(f"Using seed {random_sha256.seed}")

    random_string1 = random_sha256.generate()
    print(random_string1)

    random_string2 = random_sha256.generate()
    print(random_string2)
```

###

## Further Resources

+ The official Python style guide (https://peps.python.org/pep-0008/)
+ Python documentation on docstrings: https://www.datacamp.com/tutorial/docstrings-python
+ Typing module documentation: https://docs.python.org/
`

TODO
def upload_file_process(logged_user: LoggedUser, file_obj: object, valid_ext: list[str]) -> list[int, str, str]:

`#eof`