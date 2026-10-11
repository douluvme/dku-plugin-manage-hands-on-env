"""Base class shared by every macro (python runnable) of this plugin.

Each ``python-runnables/*/runnable.py`` does ``from managehandsonenv import base`` and
keeps a ``class MyRunnable(base.HandsOnRunnable)`` that names the feature it runs::

    from managehandsonenv import base

    class MyRunnable(base.HandsOnRunnable):
        feature_id = "duplicate_starters"

``run()`` applies the admin-project guard once, for every macro, then delegates to
the registered :class:`~managehandsonenv.features.types.Feature`.

Import the *module*, never ``from managehandsonenv.base import HandsOnRunnable``:
DSS scans the macro module for classes inheriting ``Runnable`` and refuses to load
it when it finds more than one ("Multiple classes inheriting ... Runnable").
"""
from typing import Any, Dict, Optional, Tuple

import dataiku
from dataiku.runnables import Runnable

from managehandsonenv.context import Context
from managehandsonenv.features import get_feature
from managehandsonenv.features.types import Feature
from managehandsonenv.settings import Settings  # noqa: F401  (re-exported for callers of base.Settings)


class HandsOnRunnable(Runnable):
    """Common constructor, settings, API client and admin guard for all macros."""

    #: id of the feature (see ``managehandsonenv.features``) this macro runs
    feature_id: Optional[str] = None

    def __init__(self, project_key: str, config: Optional[Dict[str, Any]], plugin_config: Optional[Dict[str, Any]]):
        self.project_key = project_key
        self.config = config or {}
        self.plugin_config = plugin_config or {}
        self.settings = Settings.from_plugin_config(self.plugin_config)
        self.client = dataiku.api_client()
        self.context = Context(
            client=self.client,
            settings=self.settings,
            plugin_config=self.plugin_config,
            project_key=self.project_key,
            component_config=self.config,
            component_label="macro parameters",
        )

    @property
    def feature(self) -> Feature:
        if self.feature_id is None:
            raise NotImplementedError("{} sets no feature_id".format(type(self).__name__))
        return get_feature(self.feature_id)

    def get_progress_target(self) -> Optional[Tuple[int, str]]:
        feature = self.feature
        if feature.progress_target is None:
            return None
        target = feature.progress_target(self.context, self.config)
        return None if target is None else (target, 'NONE')

    def run(self, progress_callback):
        if self.project_key != self.settings.admin_project_key:
            raise RuntimeError(
                "This macro can only be run from project {} (current project: {})".format(
                    self.settings.admin_project_key, self.project_key
                )
            )
        return self.execute(progress_callback)

    def execute(self, progress_callback):
        return self.feature.run(self.context, self.config, progress_callback)

    def aws_preset(self) -> Dict[str, Any]:
        """The ``aws_account`` preset: plugin-level first, then the macro's own parameter."""
        return self.context.aws_preset()
