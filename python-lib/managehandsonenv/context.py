"""The execution context handed to every feature function.

A :class:`Context` bundles what a feature needs regardless of who calls it:
the DSS API client, the plugin :class:`~managehandsonenv.settings.Settings`,
the raw ``plugin_config`` (for the AWS preset), the key of the project the
caller runs in, and a ``log`` callable. Macros build one in
``HandsOnRunnable``; the webapp backend builds one per job.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from managehandsonenv.settings import Settings


@dataclass
class Context:
    client: Any
    settings: Settings = field(default_factory=Settings)
    plugin_config: Dict[str, Any] = field(default_factory=dict)
    project_key: str = ""
    log: Callable[[str], None] = print

    def aws_preset(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """The ``aws_account`` preset: plugin-level first, then the caller's own parameter."""
        for source in (self.plugin_config, params or {}):
            preset = source.get("aws_account")
            if isinstance(preset, dict) and preset.get("aws_access_key_id"):
                return preset
        return {}

    @property
    def is_admin_project(self) -> bool:
        """True when the caller runs inside the admin project the plugin is restricted to."""
        return self.project_key == self.settings.admin_project_key
