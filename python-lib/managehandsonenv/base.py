"""Shared base class and plugin-level settings for every macro (python runnable) in this plugin."""
from dataclasses import dataclass, fields

import dataiku
from dataiku.runnables import Runnable


@dataclass(frozen=True)
class Settings:
    """Environment-specific values, read from the plugin settings (``plugin_config``).

    Every field has a default so a macro keeps working on an instance where the
    plugin settings were never filled in. Field names match the STRING params
    declared in ``plugin.json``; an empty or missing value falls back to the default.
    """

    admin_project_key: str = "ADMINV4"
    sandbox_folder: str = "SANDBOX"
    aws_region: str = "ap-northeast-2"
    rds_instance_id: str = "postgres-mag"
    api_node_instance_id: str = "i-0e7ccb12c93ac1df2"
    readonly_project_key: str = "READONLY"
    shared_dataset_name: str = "credit_score"
    protected_bundle_prefix: str = "READONLY"

    @classmethod
    def from_plugin_config(cls, plugin_config):
        plugin_config = plugin_config or {}
        values = {}
        for field in fields(cls):
            value = plugin_config.get(field.name)
            if isinstance(value, str):
                value = value.strip()
            if value:
                values[field.name] = value
        return cls(**values)


class HandsOnRunnable(Runnable):
    """Base class for the hands-on macros.

    Every ``runnable.py`` keeps a ``class MyRunnable(HandsOnRunnable)`` because
    DSS loads the runnable by that name. Subclasses implement :meth:`execute`
    instead of :meth:`run`; :meth:`run` enforces that the macro is launched
    from the admin project and then delegates to :meth:`execute`.

    Subclasses that report progress override :meth:`get_progress_target`.
    """

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config or {}
        self.plugin_config = plugin_config or {}
        self.settings = Settings.from_plugin_config(self.plugin_config)
        self.client = dataiku.api_client()

    @property
    def admin_project_key(self):
        return self.settings.admin_project_key

    def aws_preset(self):
        """The ``aws-credentials`` preset dict, from the plugin settings or the macro's own params."""
        return self.plugin_config.get("aws_account") or self.config.get("aws_account") or {}

    def get_progress_target(self):
        """Return ``(target, unit)`` with unit in SIZE/FILES/RECORDS/NONE, or None."""
        return None

    def run(self, progress_callback):
        """Guard against running outside the admin project, then run :meth:`execute`."""
        if self.project_key != self.admin_project_key:
            raise RuntimeError(
                f"This macro can only be run from project {self.admin_project_key} "
                f"(current project: {self.project_key})"
            )
        return self.execute(progress_callback)

    def execute(self, progress_callback):
        """Macro body. ``progress_callback`` expects one value: the current progress."""
        raise NotImplementedError
