"""Form schema of a feature, derived from its macro's ``runnable.json``.

The webapp renders the same parameters DSS shows for the macro, so there is one
definition of each feature's options. PRESET parameters (the AWS account) are
not shown: the backend takes them from the webapp or plugin settings, and the
form only says where they come from.

The descriptors are read from the generated snapshot
``managehandsonenv.features.descriptor_data`` rather than from the files: DSS
runs a plugin webapp backend from a copy of the plugin that holds python-lib/
but not python-runnables/.
"""
from typing import Any, Dict, List, Optional

from managehandsonenv.features.descriptor_data import MACRO_DESCRIPTORS
from managehandsonenv.features.types import Feature
from managehandsonenv.settings import Settings
from managehandsonenv.starters import STARTERS

#: parameter types the front end knows how to render; anything else is shown as a text input
RENDERABLE_TYPES = {"INT", "DOUBLE", "STRING", "PASSWORD", "TEXTAREA", "BOOLEAN", "SELECT", "MULTISELECT", "STRINGS"}
HIDDEN_TYPES = {"PRESET"}
COPIED_KEYS = ("name", "label", "description", "defaultValue", "mandatory", "visibilityCondition", "allowDuplicates")

#: webapp-only wording for a few macro labels; the descriptors (and the DSS macro forms) keep theirs
LABEL_OVERRIDES = {
    ("2-1-delete-starter-projects", "delete_TF"): "Perform deletion",
    ("1-2-change-owner-starter-projects", "admin_TF"): "Set owner back to admin",
    ("3-1-modify-db-class", "wait_TF"): "Wait until the change completes",
}

#: how the plugin settings read on the form ("RDS instance · postgres-mag")
SETTING_LABELS = {
    "admin_project_key": "Admin project",
    "sandbox_folder": "Sandbox folder",
    "aws_region": "AWS region",
    "rds_instance_id": "RDS instance",
    "api_node_instance_id": "API node instance",
    "readonly_project_key": "Read-only project",
    "shared_dataset_name": "Shared dataset",
    "protected_bundle_prefix": "Protected prefix",
}


def param_schema(param: Dict[str, Any], macro_folder: Optional[str] = None) -> Dict[str, Any]:
    """One parameter of the form, as the front end expects it."""
    schema = {key: param[key] for key in COPIED_KEYS if key in param}
    override = LABEL_OVERRIDES.get((macro_folder, param.get("name")))
    if override:
        schema["label"] = override
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


def settings_chips(feature: Feature, settings: Optional[Settings]) -> List[Dict[str, str]]:
    """The plugin settings the feature acts on, for display next to its form."""
    if settings is None:
        return []
    values = settings.public_dict()
    return [
        {"key": key, "label": SETTING_LABELS.get(key, key), "value": str(values[key])}
        for key in feature.settings_used if key in values
    ]


def uses_aws(feature: Feature) -> bool:
    """True for the features that build a boto3 client (they all read the AWS region)."""
    return "aws_region" in feature.settings_used


def aws_chip(aws_source: Optional[str]) -> Dict[str, Any]:
    """The chip saying where the AWS credentials come from (or that none are configured)."""
    if aws_source:
        return {"key": "aws_account", "label": "AWS account", "value": aws_source}
    return {"key": "aws_account", "label": "AWS account", "value": "not set", "missing": True,
            "hint": "Select an AWS Account in the webapp settings (Settings tab), then restart the backend."}


def form_schema(feature: Feature, descriptor: Dict[str, Any] = None,
                settings: Optional[Settings] = None, aws_source: Optional[str] = None) -> Dict[str, Any]:
    """``{"feature_id", "label", "description", "destructive", "confirm", "params": [...], "settings": [...]}``.

    ``aws_source`` is where the backend finds the AWS credentials (``Context.aws_preset_source``);
    the features that use AWS get a chip for it, flagged ``missing`` when there are none.
    """
    if descriptor is None:
        try:
            descriptor = MACRO_DESCRIPTORS[feature.macro_folder]
        except KeyError:
            raise KeyError("No descriptor snapshot for macro folder {!r}: run `make sync`".format(feature.macro_folder))
    params: List[Dict[str, Any]] = [
        param_schema(param, feature.macro_folder)
        for param in descriptor.get("params", [])
        if param.get("type") not in HIDDEN_TYPES and param.get("name")
    ]
    return {
        "feature_id": feature.id,
        "label": feature.display_label,
        "macro_label": feature.label,
        "menu_label": feature.menu_label_or_label,
        "category": feature.display_category,
        "description": feature.description or descriptor.get("meta", {}).get("description", ""),
        "destructive": feature.destructive,
        "confirm": feature.confirm,
        "params": params,
        "settings": settings_chips(feature, settings) + ([aws_chip(aws_source)] if uses_aws(feature) else []),
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
