"""Plugin-level settings (``plugin_config``) shared by the macros and the webapp."""
from dataclasses import dataclass, fields
from typing import Any, Dict, Optional


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

    def public_dict(self) -> Dict[str, str]:
        """The settings as a plain dict (none of them is a secret)."""
        return {field.name: getattr(self, field.name) for field in fields(self)}
