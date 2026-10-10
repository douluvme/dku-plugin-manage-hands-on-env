#!/usr/bin/env python3
"""Validate the plugin descriptors and component layout without a DSS instance.

Checks plugin.json, parameter-sets/*/parameter-set.json, python-runnables/*/runnable.json
and webapps/*/webapp.json:

- the files parse once // and /* */ comments are stripped (string-aware);
  `#` comments are rejected because they are not valid in DSS descriptors
- no duplicate keys anywhere (a last-wins parser would silently drop params)
- parameter names are unique and PRESET params reference an existing
  parameter set
- every macro folder has a runnable.py defining `class MyRunnable(base.HandsOnRunnable)`,
  importing the base *module* (`from managehandsonenv import base`; importing the
  class itself makes DSS reject the macro with "Multiple classes inheriting
  Runnable") and naming a `feature_id` that exists in managehandsonenv.features
- the starter-project parameters use getChoicesFromPython (no selectChoices),
  their descriptor names a paramsPythonSetup script, and that script exists
  under resource/ and defines `do(`
- every webapp folder has backend.py, body.html, app.js and style.css
- the descriptor snapshot the webapp reads (features/descriptor_data.py) is up to date

Exit status is 1 when anything is wrong.
"""
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python-lib"))

from managehandsonenv.descriptors import DescriptorError, load_descriptor, strip_comments  # noqa: E402
from managehandsonenv.features import FEATURES  # noqa: E402


def _load_sync_script():
    spec = importlib.util.spec_from_file_location("sync_feature_params", ROOT / "scripts" / "sync_feature_params.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# macro folder -> parameter that must take its choices from python (starters.py)
STARTER_PARAMS = {
    "1-1-duplicate-starter-projects": "project_keys_list",
    "1-2-change-owner-starter-projects": "project_key_select",
    "2-1-delete-starter-projects": "project_keys_list",
}

WEBAPP_FILES = ("backend.py", "body.html", "app.js", "style.css")

parse_descriptor = load_descriptor  # kept for callers of the old name


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


def check_python_setup(data, where, errors):
    """A component using getChoicesFromPython must name a resource/ script that defines do()."""
    setup = data.get("paramsPythonSetup")
    if not setup:
        errors.append("{}: uses getChoicesFromPython but declares no paramsPythonSetup "
                      "(DSS: \"doesn't declare python setup code\")".format(where))
        return
    script = ROOT / "resource" / setup
    if not script.is_file():
        errors.append("{}: paramsPythonSetup {!r} not found at {}".format(where, setup, script.relative_to(ROOT)))
        return
    if not re.search(r"^def do\(", script.read_text(encoding="utf-8"), re.M):
        errors.append("{}: must define `do(payload, config, plugin_config, inputs)`".format(script.relative_to(ROOT)))


def check_runnable_source(source, rel, errors):
    """The runnable.py conventions DSS and the feature registry rely on."""
    if not re.search(r"^class MyRunnable\(base\.HandsOnRunnable\):", source, re.M):
        errors.append("{}: runnable.py must define `class MyRunnable(base.HandsOnRunnable):`".format(rel))
    if re.search(r"^from managehandsonenv\.base import", source, re.M):
        errors.append("{}: runnable.py must `from managehandsonenv import base`, not import names from it "
                      "(DSS: \"Multiple classes inheriting Runnable\")".format(rel))
    match = re.search(r"^\s+feature_id\s*=\s*[\"'](\w+)[\"']", source, re.M)
    if not match:
        errors.append("{}: runnable.py must set `feature_id = \"...\"` on MyRunnable".format(rel))
    elif match.group(1) not in FEATURES:
        errors.append("{}: feature_id {!r} is not registered in managehandsonenv.features (known: {})".format(
            rel, match.group(1), list(FEATURES)))
    elif FEATURES[match.group(1)].macro_folder != rel.name:
        errors.append("{}: feature {!r} is registered for macro folder {!r}".format(
            rel, match.group(1), FEATURES[match.group(1)].macro_folder))


def main():
    errors = []
    checked = 0

    def load(path):
        nonlocal checked
        try:
            data = load_descriptor(path)
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

    macro_folders = set()
    for folder in sorted(p for p in (ROOT / "python-runnables").iterdir() if p.is_dir()):
        rel = folder.relative_to(ROOT)
        macro_folders.add(folder.name)
        descriptor = folder / "runnable.json"
        code = folder / "runnable.py"
        if not descriptor.exists():
            errors.append("{}: runnable.json is missing".format(rel))
            continue
        if not code.exists():
            errors.append("{}: runnable.py is missing".format(rel))
            continue
        check_runnable_source(code.read_text(encoding="utf-8"), rel, errors)

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
            check_python_setup(data, str(rel), errors)

    for feature in FEATURES.values():
        if feature.macro_folder not in macro_folders:
            errors.append("feature {!r} points at missing macro folder {!r}".format(feature.id, feature.macro_folder))

    webapps_dir = ROOT / "webapps"
    if webapps_dir.is_dir():
        for folder in sorted(p for p in webapps_dir.iterdir() if p.is_dir()):
            rel = folder.relative_to(ROOT)
            descriptor = folder / "webapp.json"
            if not descriptor.exists():
                errors.append("{}: webapp.json is missing".format(rel))
                continue
            data = load(descriptor)
            if data is None:
                continue
            check_params(data.get("params", []), parameter_sets, str(rel), errors)
            for name in WEBAPP_FILES:
                if not (folder / name).is_file():
                    errors.append("{}: {} is missing".format(rel, name))
            if str(data.get("hasBackend", "")).lower() != "true":
                errors.append("{}: webapp.json must set \"hasBackend\": \"true\" (backend.py serves the API)".format(rel))

    sync = _load_sync_script()
    if not sync.TARGET.exists() or sync.TARGET.read_text(encoding="utf-8") != sync.render(sync.collect()):
        errors.append("{}: descriptor snapshot is stale or missing; run `make sync`".format(
            sync.TARGET.relative_to(ROOT)))

    for error in errors:
        print("ERROR: {}".format(error))
    print("{} descriptor(s) checked, {} error(s)".format(checked, len(errors)))
    return 1 if errors else 0


__all__ = ["DescriptorError", "strip_comments", "parse_descriptor", "main"]

if __name__ == "__main__":
    sys.exit(main())
