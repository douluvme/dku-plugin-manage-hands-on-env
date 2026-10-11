# Backend of the "Hands-on Workshop Console" plugin webapp.
#
# DSS runs this file with a Flask ``app`` already defined. Everything else lives in
# python-lib (managehandsonenv.webapp): this file only wires the DSS runtime to it.
import dataiku

from managehandsonenv.context import Context
from managehandsonenv.settings import Settings
from managehandsonenv.webapp.api import register_routes
from managehandsonenv.webapp.jobs import JobManager

PLUGIN_ID = "manage-hands-on-env"

try:
    from dataiku.customwebapp import get_plugin_config
except ImportError:  # older DSS: read the plugin settings through the public API instead
    get_plugin_config = None
try:
    from dataiku.customwebapp import get_webapp_config
except ImportError:  # pragma: no cover - depends on the DSS version
    get_webapp_config = None

AWS_PARAMETER_SET = "aws-credentials"


def has_aws_keys(preset):
    return isinstance(preset, dict) and bool(preset.get("aws_access_key_id"))


def resolve_plugin_preset(plugin_config):
    """Replace an unresolved plugin-level ``aws_account`` reference by the preset's values.

    ``get_plugin_config()`` may hand a PRESET parameter as ``{"mode": "PRESET", "name": ...}``
    instead of the parameter set's values. Best effort: look the name up in the plugin
    settings through the public API; anything that fails leaves the config as it is.
    """
    ref = plugin_config.get("aws_account")
    if has_aws_keys(ref) or not isinstance(ref, dict) or not ref.get("name"):
        return plugin_config
    try:
        raw = dataiku.api_client().get_plugin(PLUGIN_ID).get_settings().get_raw()
        for preset in raw.get("presets", []):
            if preset.get("type") == AWS_PARAMETER_SET and preset.get("name") == ref["name"]:
                if has_aws_keys(preset.get("config")):
                    resolved = dict(plugin_config)
                    resolved["aws_account"] = preset["config"]
                    return resolved
                print("Plugin preset {!r} carries no AWS access key id".format(ref["name"]))
    except Exception as e:  # pragma: no cover - depends on the DSS runtime
        print("Could not resolve the plugin-level AWS preset {!r} ({})".format(ref.get("name"), e))
    return plugin_config


def load_plugin_config():
    """The plugin-level settings (admin project, sandbox folder, AWS preset, ...)."""
    if get_plugin_config is not None:
        try:
            return get_plugin_config() or {}
        except Exception as e:  # pragma: no cover - depends on the DSS runtime
            print("get_plugin_config() failed ({}); falling back to the plugin API".format(e))
    try:
        raw = dataiku.api_client().get_plugin(PLUGIN_ID).get_settings().get_raw()
        return raw.get("config") or {}
    except Exception as e:  # pragma: no cover - depends on the DSS runtime
        print("Could not read the plugin settings ({}); using defaults".format(e))
        return {}


def load_webapp_config():
    """This webapp instance's own settings (the AWS Account preset, resolved by DSS)."""
    if get_webapp_config is None:
        return {}
    try:
        return get_webapp_config() or {}
    except Exception as e:  # pragma: no cover - depends on the DSS runtime
        print("get_webapp_config() failed ({}); the webapp settings are ignored".format(e))
        return {}


PROJECT_KEY = dataiku.default_project_key()
PLUGIN_CONFIG = resolve_plugin_preset(load_plugin_config())
WEBAPP_CONFIG = load_webapp_config()
SETTINGS = Settings.from_plugin_config(PLUGIN_CONFIG)


def make_context():
    return Context(
        client=dataiku.api_client(),
        settings=SETTINGS,
        plugin_config=PLUGIN_CONFIG,
        project_key=PROJECT_KEY,
        component_config=WEBAPP_CONFIG,
        component_label="webapp settings",
    )


MANAGER = JobManager(make_context)
register_routes(app, MANAGER, make_context)  # noqa: F821  (``app`` is injected by DSS)

print("Hands-on console backend ready in project {} (admin project: {}, AWS credentials: {})".format(
    PROJECT_KEY, SETTINGS.admin_project_key, make_context().aws_preset_source() or "not configured"))
