#!/usr/bin/env python3
"""Validate the plugin's JSON descriptors without a DSS instance.

DSS accepts ``//`` and ``/* */`` comments in descriptors, so those are stripped
before parsing. Anything else that standard JSON rejects (``#`` comments,
trailing commas) fails, as does a duplicate key at any nesting level, which a
last-wins parser would silently resolve (this is how 3-1's second "params"
array once hid the db_class/wait_TF parameters).

Usage: python3 scripts/check_descriptors.py [plugin root]   (default: repo root)
Exit status is non-zero when any descriptor is invalid.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent)

DESCRIPTOR_GLOBS = (
    "plugin.json",
    "parameter-sets/*/parameter-set.json",
    "python-runnables/*/runnable.json",
)

# Strings first so a "//" or "/*" inside a string value is left alone.
_TOKEN = re.compile(
    r'"(?:\\.|[^"\\])*"'       # JSON string
    r'|/\*.*?\*/'              # block comment
    r'|//[^\n]*',              # line comment
    re.DOTALL,
)


def strip_comments(text):
    return _TOKEN.sub(lambda m: m.group(0) if m.group(0).startswith('"') else "", text)


def reject_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate key {key!r}")
        seen[key] = value
    return seen


def check(path):
    text = path.read_text(encoding="utf-8")
    data = json.loads(strip_comments(text), object_pairs_hook=reject_duplicates)
    problems = []

    if path.name == "runnable.json":
        names = [p.get("name") for p in data.get("params", [])]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            problems.append(f"duplicate param name(s): {dupes}")
        for p in data.get("params", []):
            if p.get("type") == "PRESET":
                preset_dir = ROOT / "parameter-sets" / p.get("parameterSetId", "")
                if not (preset_dir / "parameter-set.json").is_file():
                    problems.append(f"param {p.get('name')!r} references unknown preset {p.get('parameterSetId')!r}")
        if not (path.parent / "runnable.py").is_file():
            problems.append("no runnable.py next to it")

    if path.name == "plugin.json":
        for p in data.get("params", []):
            if p.get("type") == "PRESET":
                preset_dir = ROOT / "parameter-sets" / p.get("parameterSetId", "")
                if not (preset_dir / "parameter-set.json").is_file():
                    problems.append(f"plugin param {p.get('name')!r} references unknown preset {p.get('parameterSetId')!r}")

    return problems


def main():
    failed = 0
    paths = [p for g in DESCRIPTOR_GLOBS for p in sorted(ROOT.glob(g))]
    if not paths:
        print(f"no descriptors found under {ROOT}")
        return 1
    for path in paths:
        rel = path.relative_to(ROOT)
        try:
            problems = check(path)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"FAIL {rel}: {e}")
            failed += 1
            continue
        if problems:
            failed += 1
            for problem in problems:
                print(f"FAIL {rel}: {problem}")
        else:
            print(f"ok   {rel}")
    print(f"{len(paths) - failed}/{len(paths)} descriptors valid")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
