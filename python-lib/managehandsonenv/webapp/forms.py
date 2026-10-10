"""Form schema of a feature, derived from its macro's ``runnable.json``.

The webapp renders the same parameters DSS shows for the macro, so there is one
definition of each feature's options. PRESET parameters (the AWS account) are
not shown: the backend takes them from the plugin settings.

The descriptors are read from the generated snapshot
``managehandsonenv.features.descriptor_data`` rather than from the files: DSS
runs a plugin webapp backend from a copy of the plugin that holds python-lib/
but not python-runnables/.
"""
from typing import Any, Dict, List

from managehandsonenv.features.descriptor_data import MACRO_DESCRIPTORS
from managehandsonenv.features.types import Feature
from managehandsonenv.starters import STARTERS

#: parameter types the front end knows how to render; anything else is shown as a text input
RENDERABLE_TYPES = {"INT", "DOUBLE", "STRING", "PASSWORD", "TEXTAREA", "BOOLEAN", "SELECT", "MULTISELECT", "STRINGS"}
HIDDEN_TYPES = {"PRESET"}
COPIED_KEYS = ("name", "label", "description", "defaultValue", "mandatory", "visibilityCondition", "allowDuplicates")


def param_schema(param: Dict[str, Any]) -> Dict[str, Any]:
    """One parameter of the form, as the front end expects it."""
    schema = {key: param[key] for key in COPIED_KEYS if key in param}
    param_type = param.get("type", "STRING")
    schema["type"] = param_type if param_type in RENDERABLE_TYPES else "STRING"
    if param_type not in RENDERABLE_TYPES:
        schema["unsupportedType"] = param_type
    if param_type in ("SELECT", "MULTISELECT"):
        if param.get("getChoicesFromPython"):
            schema["choices"] = [dict(choice) for choice in STARTERS]
        else:
            schema["choices"] = [dict(choice) for choice in param.get("selectChoices", [])]
    return schema


def form_schema(feature: Feature, descriptor: Dict[str, Any] = None) -> Dict[str, Any]:
    """``{"feature_id", "label", "description", "destructive", "confirm", "params": [...]}``."""
    if descriptor is None:
        try:
            descriptor = MACRO_DESCRIPTORS[feature.macro_folder]
        except KeyError:
            raise KeyError("No descriptor snapshot for macro folder {!r}: run `make sync`".format(feature.macro_folder))
    params: List[Dict[str, Any]] = [
        param_schema(param)
        for param in descriptor.get("params", [])
        if param.get("type") not in HIDDEN_TYPES and param.get("name")
    ]
    return {
        "feature_id": feature.id,
        "label": feature.label,
        "category": feature.category,
        "description": feature.description or descriptor.get("meta", {}).get("description", ""),
        "destructive": feature.destructive,
        "confirm": feature.confirm,
        "params": params,
    }


def coerce_params(schema: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
    """Apply defaults and convert the JSON values the page sends to the types the features expect."""
    params = dict(values or {})
    for param in schema["params"]:
        name = param["name"]
        param_type = param["type"]
        if name not in params or params[name] is None or params[name] == "":
            if "defaultValue" in param:
                params[name] = param["defaultValue"]
            elif param_type == "BOOLEAN":
                params[name] = False
            elif param_type in ("MULTISELECT", "STRINGS"):
                params[name] = []
            else:
                continue
        value = params[name]
        if param_type == "INT":
            params[name] = int(value)
        elif param_type == "DOUBLE":
            params[name] = float(value)
        elif param_type == "BOOLEAN":
            params[name] = value if isinstance(value, bool) else str(value).lower() in ("true", "1", "yes", "on")
        elif param_type in ("MULTISELECT", "STRINGS"):
            if isinstance(value, str):
                value = [line.strip() for line in value.splitlines()]
            params[name] = [str(v) for v in value if str(v).strip()]
    return params
