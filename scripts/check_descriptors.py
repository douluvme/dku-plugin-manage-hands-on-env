#!/usr/bin/env python3
"""Static validation of the plugin's JSON descriptors.

DSS accepts ``//``, ``/* */`` and ``#`` comments in descriptors, which plain
``json.loads`` does not. This script strips the comments, parses every
descriptor with a duplicate-key check (a last-wins parser silently dropped
params in the past) and asserts that the three macros that pick starter
projects get their choices from ``managehandsonenv.starters`` instead of a
copy-pasted ``selectChoices`` list: the param sets ``getChoicesFromPython``
and the descriptor names a ``paramsPythonSetup`` script that exists under
``resource/`` and defines ``do()`` (otherwise DSS refuses the component with
"doesn't declare python setup code").

Usage: ``python3 scripts/check_descriptors.py`` from anywhere; exits 1 on failure.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: (descriptor path, name of the param that must use getChoicesFromPython)
STARTER_PARAMS = (
    ("python-runnables/1-1-duplicate-starter-projects/runnable.json", "project_keys_list"),
    ("python-runnables/1-2-change-owner-starter-projects/runnable.json", "project_key_select"),
    ("python-runnables/2-1-delete-starter-projects/runnable.json", "project_keys_list"),
)


def strip_comments(text):
    """Remove ``//``, ``#`` line comments and ``/* */`` block comments outside strings."""
    out = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if text.startswith("//", i) or ch == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                raise ValueError("unterminated block comment")
            # keep newlines so json error positions stay meaningful
            out.append("\n" * text.count("\n", i, end))
            i = end + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def reject_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate key {key!r}")
        seen[key] = value
    return seen


def load_descriptor(path):
    return json.loads(strip_comments(path.read_text(encoding="utf-8")),
                      object_pairs_hook=reject_duplicates)


def check_python_setup(descriptor, rel):
    """A component using getChoicesFromPython must name a resource/ script that defines do()."""
    setup = descriptor.get("paramsPythonSetup")
    if not setup:
        return [f"{rel}: uses getChoicesFromPython but declares no paramsPythonSetup "
                f"(DSS: \"doesn't declare python setup code\")"]
    script = ROOT / "resource" / setup
    if not script.is_file():
        return [f"{rel}: paramsPythonSetup {setup!r} not found at {script.relative_to(ROOT)}"]
    if not any(line.startswith("def do(") for line in script.read_text(encoding="utf-8").splitlines()):
        return [f"{script.relative_to(ROOT)}: must define `do(payload, config, plugin_config, inputs)`"]
    return []


def descriptor_paths():
    yield ROOT / "plugin.json"
    yield from sorted((ROOT / "parameter-sets").glob("*/parameter-set.json"))
    yield from sorted((ROOT / "python-runnables").glob("*/runnable.json"))


def main():
    errors = []
    parsed = {}

    for path in descriptor_paths():
        rel = path.relative_to(ROOT)
        try:
            parsed[str(rel)] = load_descriptor(path)
            print(f"ok   {rel}")
        except ValueError as e:
            errors.append(f"{rel}: {e}")
            print(f"FAIL {rel}: {e}")

    for rel, param_name in STARTER_PARAMS:
        descriptor = parsed.get(rel)
        if descriptor is None:
            continue  # already reported as a parse failure
        params = {p.get("name"): p for p in descriptor.get("params", [])}
        param = params.get(param_name)
        if param is None:
            errors.append(f"{rel}: param {param_name!r} not found")
        elif "selectChoices" in param:
            errors.append(f"{rel}: param {param_name!r} still has a hard-coded selectChoices list")
        elif param.get("getChoicesFromPython") is not True:
            errors.append(f"{rel}: param {param_name!r} must set \"getChoicesFromPython\": true")
        errors.extend(check_python_setup(descriptor, rel))

    if errors:
        print("\n" + "\n".join(errors))
        return 1
    print(f"\n{len(parsed)} descriptor(s) valid; starter params use getChoicesFromPython")
    return 0


if __name__ == "__main__":
    sys.exit(main())
