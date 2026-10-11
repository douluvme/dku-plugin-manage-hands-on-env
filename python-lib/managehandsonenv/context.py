"""The execution context handed to every feature function.

A :class:`Context` bundles what a feature needs regardless of who calls it:
the DSS API client, the plugin :class:`~managehandsonenv.settings.Settings`,
the raw ``plugin_config`` and the calling component's own config (both may
carry the AWS preset), the key of the project the caller runs in, and a ``log``
callable. Macros build one in ``HandsOnRunnable``; the webapp backend builds one
per job.
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
    #: the calling component's own config: a macro's parameters, the webapp's settings
    component_config: Dict[str, Any] = field(default_factory=dict)
    #: how that config is called when reporting where the AWS credentials come from
    component_label: str = "component settings"

    def _aws_preset_candidates(self, params: Optional[Dict[str, Any]]):
        yield "plugin settings", self.plugin_config
        yield self.component_label, self.component_config
        yield "run parameters", params or {}

    def aws_preset(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """The ``aws_account`` preset: plugin settings first, then the component's config, then ``params``.

        A DSS PRESET parameter arrives resolved, as a dict holding the parameter set's
        values; an unresolved reference (``{"mode": "PRESET", "name": ...}``) or an
        empty preset is skipped.
        """
        for _source, config in self._aws_preset_candidates(params):
            preset = (config or {}).get("aws_account")
            if isinstance(preset, dict) and preset.get("aws_access_key_id"):
                return preset
        return {}

    def aws_preset_source(self, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Where :meth:`aws_preset` finds the credentials (``"plugin settings"``, ...), or None."""
        for source, config in self._aws_preset_candidates(params):
            preset = (config or {}).get("aws_account")
            if isinstance(preset, dict) and preset.get("aws_access_key_id"):
                return source
        return None

    @property
    def is_admin_project(self) -> bool:
        """True when the caller runs inside the admin project the plugin is restricted to."""
        return self.project_key == self.settings.admin_project_key
