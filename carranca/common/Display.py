"""
Equipe da Canoa -- 2024

Simple colored print to screen

mgd 2024-09-27,10-11,12-05
F
"""

# cSpell:ignore colorfy

import time
from math import log10, modf
from enum import Enum
from typing import List
from platform import uname
from ..helpers.py_helper import is_str_none_or_empty, OS_IS_WINDOWS

# Alternative
# def __init__(self, **kwargs):
#     self.prompt = kwargs.get('prompt', "")
#     self.mute = kwargs.get('mute_all', False)
#     self.debug_output = kwargs.get('debug_output', False)
#     self.icon_output = kwargs.get('icon_output', True)
#     self.colors = kwargs.get('colors', [])
#     self.icons = kwargs.get('icons', [])
#     self.with_color = kwargs.get('with_color', None)


class Display:
    class Default:
        def __init__(
            self,
            prompt="",
            mute_all=False,
            debug_output=False,
            icon_output=True,
            colors=None,
            icons=None,
            with_color=None,
        ):
            self.prompt = prompt
            self.mute = mute_all
            self.debug_output = debug_output
            self.icon_output = icon_output
            self.colors = colors
            self.icons = icons
            self.with_color = with_color

    class Kind(Enum):
        PROMPT = 0
        ELAPSED = 1
        SIMPLE = 2
        INFO = 3
        WARN = 4
        ERROR = 5
        DEBUG = 6

    #  EXCEPT = 7 # todo, call

    # https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters
    def code(color_code: int):
        #       reset                 return ESC only        valid Set foreground color code
        if not ((color_code == 0) or (color_code is None) or (color_code in range(30, 37))):
            ValueError("Invalid color code, valid values are in [30, 37].")

        return "\033[" + ("" if color_code is None else f"{color_code}m")

    no_color = ""
    reset_color = code(0)
    ESC = code(None)
    elapsed_format = [f"{{:0{i}}}" for i in range(1, 6)]
    with_color = True
    try:
        # https://en.wikipedia.org/wiki/ANSI_escape_code#DOS_and_Windows
        # Since 2016! Windows 10 version 1511 -> Windows has colors
        # Sommelier > Windows v 6.2.9200
        with_color = (int(uname().version.split(".")[0]) > 9) if OS_IS_WINDOWS else True
    except:
        with_color = not OS_IS_WINDOWS

    default = Default(
        # keep same order as Display.__init__
        "",
        False,
        False,
        True,
        [
            # https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit
            code(36),  # Prompt gray
            code(90),  # elapsed 999:ss:mm
            no_color,  # Simple
            code(32),  # Info green
            code(33),  # Warn yellow
            code(31),  # Error red
            code(35),  # Debug Magenta
        ],
        [
            "",  # Prompt
            "",  # elapsed format
            "",  # Simple
            "[i] ",  # Info
            "[▲] ",  # Warn
            "[!] ",  # Error
            "[¤] ",  # Debug
        ],
        None,  # with_color (bool, use color)
    )

    def debug_output() -> bool:
        return Display.default.debug_output

    def icon_output() -> bool:
        return Display.default.icon_output

    def __init__(
        self,
        # keep same order as Display.Default
        prompt: str = None,
        mute_all: bool = False,
        debug_output: bool = None,
        icon_output: bool = None,
        elapsed_from: float = None,
        colors: List[str] = None,
        icons: List[str] = None,
        with_color: bool = None,
    ):
        _d = Display.default  # value is None => use default
        self.prompt = _d.prompt if prompt is None else prompt
        self.mute_all = True if mute_all else False
        self.debug_output = _d.debug_output if debug_output is None else debug_output
        self.icon_output = _d.icon_output if icon_output is None else icon_output
        self.elapsed_output = elapsed_from is not None
        self.elapsed_from = elapsed_from if self.elapsed_output else time.perf_counter()
        self.colors = _d.colors if colors is None else colors
        self.icons = _d.icons if icons is None else icons
        self.with_color = Display.with_color if with_color is None else bool(with_color)
        k_error = "Parameter '{0}' must be a list of Display.Kind items."
        if colors is not None and not (len(colors) == len(Display.Kind) or len(colors) == 0):
            raise ValueError(k_error.format("colors"))

        if icons is not None and len(icons) != len(Display.Kind):
            raise ValueError(k_error.format("icons"))

    def color_for_kind(self, kind: Kind) -> str:
        return self.colors[kind.value] if self.with_color else Display.no_color

    def print(
        self, kind_or_color: Kind | str, msg: str, prompt: str = None, icon_output: bool = None
    ) -> None:
        if self.mute_all:
            return

        start_color = Display.no_color
        is_kind = isinstance(kind_or_color, Display.Kind)
        kind = kind_or_color if is_kind else Display.Kind.SIMPLE.value
        if is_str_none_or_empty(msg):
            print(msg)  # perhaps a command
            return
        elif not (is_kind or (kind_or_color is None) or isinstance(kind_or_color, str)):
            return
        elif is_kind and (kind_or_color == Display.Kind.DEBUG) and not self.debug_output:
            return
        elif kind_or_color is None:
            start_color = Display.no_color
        elif is_kind:
            start_color = self.color_for_kind(kind)
        else:
            start_color = (
                Display.no_color
                if is_str_none_or_empty(kind_or_color) or not self.with_color
                else kind_or_color
            )

        # _finalize_color = Display.no_color if se
        def _colorfy(kind: Display.Kind, text: str) -> str:
            open_color = self.color_for_kind(kind)
            if (open_color == Display.no_color) or not self.with_color:
                return text
            else:
                return f"{open_color}{text}{Display.reset_color}"

        _prompt = self.prompt if prompt is None else str(prompt)
        start_text = '' if is_str_none_or_empty(_prompt) else _colorfy(Display.Kind.PROMPT, _prompt)
        if self.elapsed_output:
            start_text = f"{start_text}{_colorfy(Display.Kind.ELAPSED, self.elapsed())} "

        _icon_output = self.icon_output if icon_output is None else bool(icon_output)

        icon = self.icons[kind.value] if _icon_output else ""
        end_color = Display.no_color if start_color == Display.no_color else Display.reset_color
        print(f"{start_text}{start_color}{icon}{msg}{end_color}")

    def simple(self, msg: str, prompt: str = None, icon_output: bool = None) -> None:
        self.print(Display.Kind.SIMPLE, msg, prompt, icon_output)

    def info(self, msg: str, prompt: str = None, icon_output: bool = None) -> None:
        self.print(Display.Kind.INFO, msg, prompt, icon_output)

    def warn(self, msg: str, prompt: str = None, icon_output: bool = None) -> None:
        self.print(Display.Kind.WARN, msg, prompt, icon_output)

    def error(self, msg: str, prompt: str = None, icon_output: bool = None) -> None:
        self.print(Display.Kind.ERROR, msg, prompt, icon_output)

    def debug(self, msg: str, prompt: str = None, icon_output: bool = None) -> None:
        self.print(Display.Kind.DEBUG, msg, prompt, icon_output)

    def set_prompt(self, value: str) -> str:
        p = self.prompt
        self.prompt = '' if is_str_none_or_empty(value) else str(value)
        return p

    def set_icon_output(self, value: bool) -> bool:
        b = self.icon_output
        self.icon_output = bool(value)
        return b

    def set_elapsed_output(self, value: bool, elapsed_from: float = None) -> bool:
        was_active = self.elapsed_output
        self.elapsed_output = bool(value)
        if elapsed_from is not None:
            self.elapsed_from = elapsed_from
        elif self.elapsed_output:
            self.elapsed_from = time.perf_counter()
        else:
            self.elapsed_from = None

        return was_active

    def elapsed(self, elapsed_to: float = None) -> str:
        if self.elapsed_from is None:
            return ""

        end = time.perf_counter() if elapsed_to is None else elapsed_to
        elapsed_seconds = end - self.elapsed_from
        minutes = int(elapsed_seconds // 60)
        seconds = elapsed_seconds % 60
        x = 0 if minutes == 0 else min(len(Display.elapsed_format) - 1, int(log10(minutes)))
        if 0 <= x and x < len(Display.elapsed_format):
            frac_part, ss = modf(seconds)
            ms = int(round(frac_part * 1000))
            result = f"{Display.elapsed_format[x].format(minutes)}:{int(ss):02}.{ms:03}"
        else:
            result = "**:**.****"

        return result


# if __name__ == "__main__":
#     from platform import uname

#     import time
#     import random

#     print(f"OS Color is `{Display().with_color}`")
#     Display().simple("a")
#     Display().simple("b")

#     print("\nClass print:")
#     for e in Display.Kind:
#         Display().print(e, e.name)

#     print("\nPrint by function:")
#     Display().simple("simple")
#     Display().info("info")
#     Display().warn("warning")
#     Display().error("error")
#     Display().debug("Debug")
#     print(f"Display.debug_output is [{Display.debug_output()}].")
#     print(f"Display.icon_output is [{Display.icon_output()}].")
#     print(f"Display.with_color is [{Display.with_color}].")

#     print("\nInstance for `canoa` with 'debug_output` active:")
#     display = Display("Canoa: ", False, True, True, time.perf_counter())  # - 580)

#     print(f"display.elapsed_output is [{display.elapsed_output}].")
#     print(f"display.debug_output is [{display.debug_output}].")
#     print(f"display.icon_output is [{display.icon_output}].")
#     print(f"display.with_color is [{display.with_color}].")
#     display.with_color = False
#     for i in range(1, 20):
#         for e in Display.Kind:
#             display.print(e, e.name)
#             display.with_color = i > 2
#             time.sleep(random.randint(0, 3))

#  eof
