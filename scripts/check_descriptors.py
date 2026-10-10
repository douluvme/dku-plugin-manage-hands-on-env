#!/usr/bin/env python3
"""Validate the plugin descriptors without a DSS instance.

Checks plugin.json, parameter-sets/*/parameter-set.json and
python-runnables/*/runnable.json:

- the files parse once // and /* */ comments are stripped (string-aware);
  `#` comments are rejected because they are not valid in DSS descriptors
- no duplicate keys anywhere (a last-wins parser would silently drop params)
- parameter names are unique and PRESET params reference an existing
  parameter set
- every macro folder has a runnable.py defining `class MyRunnable(`
- the starter-project parameters use getChoicesFromPython (no selectChoices)
  and their runnable.py defines `do(`

Exit status is 1 when anything is wrong.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# macro folder -> parameter that must take its choices from python (starters.py)
STARTER_PARAMS = {
    "1-1-duplicate-starter-projects": "project_keys_list",
    "1-2-change-owner-starter-projects": "project_key_select",
    "2-1-delete-starter-projects": "project_keys_list",
}


class DescriptorError(Exception):
    pass


def strip_comments(text):
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


def parse_descriptor(path):
    text = path.read_text(encoding="utf-8")
    clean = strip_comments(text)
    # tolerate a trailing comma before ] or } (DSS does), which json.loads would reject
    clean = re.sub(r",(\s*[\]}])", r"\1", clean)
    try:
        return json.loads(clean, object_pairs_hook=_reject_duplicates)
    except json.JSONDecodeError as e:
        raise DescriptorError("invalid JSON: {}".format(e))


def check_params(params, parameter_sets, where, errors):
    names = [p.get("name") for p in params]
    for name in names:
        if not name:
            errors.append("{}: a param has no name".format(where))
    for name in sorted({n for n in names if names.count(n) > 1}):
        errors.append("{}: param {!r} is declared more than once".format(where, name))
    for param in params:
        if param.get("type") == "PRESET":
            set_id = param.get("parameterSetId")
            if set_id not in parameter_sets:
                errors.append("{}: PRESET param {!r} references unknown parameter set {!r} (known: {})".format(
                    where, param.get("name"), set_id, sorted(parameter_sets)))


def main():
    errors = []
    checked = 0

    def load(path):
        nonlocal checked
        try:
            data = parse_descriptor(path)
            checked += 1
            return data
        except DescriptorError as e:
            errors.append("{}: {}".format(path.relative_to(ROOT), e))
            return None

    parameter_sets = set()
    for path in sorted((ROOT / "parameter-sets").glob("*/parameter-set.json")):
        if load(path) is not None:
            parameter_sets.add(path.parent.name)

    plugin = load(ROOT / "plugin.json")
    if plugin is not None:
        check_params(plugin.get("params", []), parameter_sets, "plugin.json", errors)
        if not re.match(r"^\d+\.\d+\.\d+$", str(plugin.get("version", ""))):
            errors.append("plugin.json: version {!r} is not semantic".format(plugin.get("version")))

    for folder in sorted(p for p in (ROOT / "python-runnables").iterdir() if p.is_dir()):
        rel = folder.relative_to(ROOT)
        descriptor = folder / "runnable.json"
        code = folder / "runnable.py"
        if not descriptor.exists():
            errors.append("{}: runnable.json is missing".format(rel))
            continue
        if not code.exists():
            errors.append("{}: runnable.py is missing".format(rel))
            continue
        source = code.read_text(encoding="utf-8")
        if not re.search(r"^class MyRunnable\(", source, re.M):
            errors.append("{}: runnable.py does not define `class MyRunnable(`".format(rel))

        data = load(descriptor)
        if data is None:
            continue
        params = data.get("params", [])
        check_params(params, parameter_sets, str(rel), errors)

        starter_param = STARTER_PARAMS.get(folder.name)
        if starter_param:
            param = next((p for p in params if p.get("name") == starter_param), None)
            if param is None:
                errors.append("{}: starter param {!r} is missing".format(rel, starter_param))
            else:
                if "selectChoices" in param:
                    errors.append("{}: {!r} must not hard-code selectChoices (use starters.py)".format(rel, starter_param))
                if param.get("getChoicesFromPython") is not True:
                    errors.append("{}: {!r} must set getChoicesFromPython: true".format(rel, starter_param))
            if not re.search(r"^def do\(", source, re.M):
                errors.append("{}: runnable.py must define `do(payload, config, plugin_config, inputs)`".format(rel))

    for error in errors:
        print("ERROR: {}".format(error))
    print("{} descriptor(s) checked, {} error(s)".format(checked, len(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
