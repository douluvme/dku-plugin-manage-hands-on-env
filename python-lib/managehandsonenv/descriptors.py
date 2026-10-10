"""Comment-tolerant parsing of the plugin's JSON descriptors.

DSS descriptors (``plugin.json``, ``runnable.json``, ``webapp.json`` ...) may
contain ``//`` and ``/* */`` comments and trailing commas, which ``json.loads``
rejects. This module strips them (string-aware), parses with a duplicate-key
check (a last-wins parser silently dropped params in the past) and locates the
plugin's own files, so the webapp can build forms from the macro descriptors
and ``scripts/check_descriptors.py`` can validate them.
"""
import json
import pathlib
import re
from typing import Any, Dict

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent


class DescriptorError(ValueError):
    pass


def plugin_root() -> pathlib.Path:
    """The plugin folder (``python-lib/managehandsonenv`` is two levels below it)."""
    return PACKAGE_DIR.parents[1]


def strip_comments(text: str) -> str:
    """Remove // and /* */ comments outside strings. Raises on `#` comments."""
    out = []
    i = 0
    n = len(text)
    line = 1
    in_string = False
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise DescriptorError("unterminated /* comment starting at line {}".format(line))
            line += text.count("\n", i, end)
            i = end + 2
            continue
        if c == "#":
            raise DescriptorError("`#` comment at line {} is not valid in a descriptor".format(line))
        out.append(c)
        i += 1
    return "".join(out)


def _reject_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise DescriptorError("duplicate key {!r}".format(key))
        seen[key] = value
    return seen


def parse_descriptor_text(text: str) -> Dict[str, Any]:
    clean = strip_comments(text)
    # tolerate a trailing comma before ] or } (DSS does), which json.loads would reject
    clean = re.sub(r",(\s*[\]}])", r"\1", clean)
    try:
        return json.loads(clean, object_pairs_hook=_reject_duplicates)
    except json.JSONDecodeError as e:
        raise DescriptorError("invalid JSON: {}".format(e))


def load_descriptor(path) -> Dict[str, Any]:
    return parse_descriptor_text(pathlib.Path(path).read_text(encoding="utf-8"))


def macro_descriptor(folder_name: str) -> Dict[str, Any]:
    """The parsed ``runnable.json`` of ``python-runnables/<folder_name>``."""
    return load_descriptor(plugin_root() / "python-runnables" / folder_name / "runnable.json")
