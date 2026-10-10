"""Common base class for every macro (python runnable) in this plugin."""
from dataiku.runnables import Runnable
import dataiku


class HandsOnRunnable(Runnable):
    """Base runnable: stores the DSS context, builds the API client and
    refuses to run from any project other than the admin project.

    Subclasses keep the ``MyRunnable`` class name (DSS loads it by name),
    implement :meth:`execute` and may override :meth:`get_progress_target`.

    Each ``runnable.py`` must ``from managehandsonenv import base`` and define
    ``class MyRunnable(base.HandsOnRunnable)``. Never ``from managehandsonenv.base
    import HandsOnRunnable``: DSS scans the macro module for classes inheriting
    ``Runnable`` and refuses to load it when it finds more than one.
    """

    ADMIN_PROJECT_KEY = "ADMINV4"

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        self.client = dataiku.api_client()

    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def run(self, progress_callback):
        """Entry point called by DSS. Enforces the admin-project guard, then delegates
        to :meth:`execute`."""
        if self.project_key != self.ADMIN_PROJECT_KEY:
            raise RuntimeError(
                f"This macro can only be run from project {self.ADMIN_PROJECT_KEY} "
                f"(current project: {self.project_key})"
            )
        return self.execute(progress_callback)

    def execute(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        raise NotImplementedError
