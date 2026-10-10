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


PROJECT_KEY = dataiku.default_project_key()
PLUGIN_CONFIG = load_plugin_config()
SETTINGS = Settings.from_plugin_config(PLUGIN_CONFIG)


def make_context():
    return Context(
        client=dataiku.api_client(),
        settings=SETTINGS,
        plugin_config=PLUGIN_CONFIG,
        project_key=PROJECT_KEY,
    )


MANAGER = JobManager(make_context)
register_routes(app, MANAGER, make_context)  # noqa: F821  (``app`` is injected by DSS)

print("Hands-on console backend ready in project {} (admin project: {})".format(
    PROJECT_KEY, SETTINGS.admin_project_key))
