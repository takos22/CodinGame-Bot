import textwrap
from textwrap import shorten

# ---------------------------------------------------------------------------------------------
# Formatting


def indent(text: str, amount: int, char: str = " ") -> str:
    """Indent every line of `text` by `amount` of `char` (default: `" "`)"""
    return textwrap.indent(text, amount * char)


def dedent(text: str, keepends: bool = False) -> str:
    "Removes the indent at the start of every line"
    return "".join([line.lstrip() for line in text.splitlines(keepends)])


# ---------------------------------------------------------------------------------------------
# Colors


class Colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    PURPLE = "\033[95m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    WHITE = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def color(text: str, color: str) -> str:
    color = getattr(Colors, color.upper(), "")
    if color:
        text = f"{color}{text}{Colors.END}"
    return text


def uncolor(text: str) -> str:
    colors = [
        getattr(Colors, color)
        for color in dir(Colors)
        if not color.startswith("__")
    ]
    for color in colors:
        text = text.replace(color, "")
    return text
