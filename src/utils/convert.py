import textwrap
import re
from typing import List, Union


def convert_str_to_str_list(
    text: str, width: int = 88, is_return_list: bool = True
) -> Union[List[str], str]:
    """
    Format a long docstring using semantic chunking and line wrapping.
    Breaks at paragraph boundaries and wraps lines to the given width.
    Args:
        text (str): The docstring text to format
        width (int): Maximum line width (default 88)
    Returns:
        str: Formatted docstring
    """
    # Split into sentences (by periods)
    sentences = re.findall(r".+?\. ", text.strip())

    wrapped = []

    for p in sentences:
        line = textwrap.fill(p.strip(), width=width, replace_whitespace=False)
        line_ls = line.splitlines()
        for line in line_ls:
            wrapped.append(line)

    if is_return_list:
        return wrapped

    return "\n\n".join(wrapped)


def convert_str_keep_alphanumeric(
    text_str, allowed_characters=None, replacement_character: str = ""
) -> str:
    allowed_characters = allowed_characters or r"[^0-9a-zA-Z_\-\s]+"

    return re.sub(allowed_characters, replacement_character, text_str)


def to_snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    # Insert underscores before uppercase letters, except at the start
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    # Remove any special characters except underscores
    name = re.sub(r"[^\w]", "", name)
    return name.lower()
