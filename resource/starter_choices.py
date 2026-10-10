"""Python setup code for the starter-project dropdowns (DSS dynamic select).

The three macros that offer the standard starter projects (duplicate, change
owner, delete) declare ``"paramsPythonSetup": "starter_choices.py"`` in their
runnable.json; DSS then calls ``do()`` below whenever one of their
``getChoicesFromPython`` parameters needs its choices.

The list itself lives in ``managehandsonenv.starters`` (python-lib) so that it
is defined once for every macro.
"""
import os
import sys

try:
    from managehandsonenv.starters import starter_choices
except ImportError:
    # Setup code may run without the plugin's python-lib on sys.path; add it relative to this file.
    _LIB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "python-lib")
    if _LIB_DIR not in sys.path:
        sys.path.insert(0, _LIB_DIR)
    from managehandsonenv.starters import starter_choices


def do(payload, config, plugin_config, inputs):
    """Return ``{"choices": [...]}`` for the parameter named in ``payload["parameterName"]``.

    Every parameter served by this file takes the same starter list, so the
    parameter name is not inspected.
    """
    return starter_choices()
