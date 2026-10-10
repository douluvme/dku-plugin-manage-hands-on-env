"""Base class and plugin-level settings shared by every macro of this plugin.

Each ``python-runnables/*/runnable.py`` does ``from managehandsonenv import base`` and
keeps a ``class MyRunnable(base.HandsOnRunnable)`` that implements
``execute(progress_callback)``. ``run()`` applies the admin-project guard once, for
every macro.

Import the *module*, never ``from managehandsonenv.base import HandsOnRunnable``:
DSS scans the macro module for classes inheriting ``Runnable`` and refuses to load
it when it finds more than one ("Multiple classes inheriting ... Runnable").
"""
from dataclasses import dataclass, fields
from typing import Any, Dict, Optional, Tuple

import dataiku
from dataiku.runnables import Runnable


@dataclass(frozen=True)
class Settings:
    """Environment-specific values, read from the plugin settings (``plugin_config``).

    Every field has a default matching the historical hard-coded value, so the
    plugin keeps working when the settings page was never saved.
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
    def from_plugin_config(cls, plugin_config: Optional[Dict[str, Any]]) -> "Settings":
        """Build settings from ``plugin_config``; blank or missing values keep the default."""
        plugin_config = plugin_config or {}
        values = {}
        for field in fields(cls):
            value = plugin_config.get(field.name)
            if isinstance(value, str) and value.strip():
                values[field.name] = value.strip()
        return cls(**values)


class HandsOnRunnable(Runnable):
    """Common constructor, settings, API client and admin guard for all macros."""

    def __init__(self, project_key: str, config: Optional[Dict[str, Any]], plugin_config: Optional[Dict[str, Any]]):
        self.project_key = project_key
        self.config = config or {}
        self.plugin_config = plugin_config or {}
        self.settings = Settings.from_plugin_config(self.plugin_config)
        self.client = dataiku.api_client()

    def get_progress_target(self) -> Optional[Tuple[int, str]]:
        """Subclasses override when they report progress."""
        return None

    def run(self, progress_callback):
        if self.project_key != self.settings.admin_project_key:
            raise RuntimeError(
                "This macro can only be run from project {} (current project: {})".format(
                    self.settings.admin_project_key, self.project_key
                )
            )
        return self.execute(progress_callback)

    def execute(self, progress_callback):
        raise NotImplementedError

    def aws_preset(self) -> Dict[str, Any]:
        """The ``aws_account`` preset: plugin-level first, then the macro's own parameter."""
        for source in (self.plugin_config, self.config):
            preset = source.get("aws_account")
            if isinstance(preset, dict) and preset.get("aws_access_key_id"):
                return preset
        return {}
