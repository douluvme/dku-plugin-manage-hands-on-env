"""Shared base class for every macro (python runnable) in this plugin."""
import dataiku
from dataiku.runnables import Runnable


class HandsOnRunnable(Runnable):
    """Base class for the hands-on macros.

    Every ``runnable.py`` keeps a ``class MyRunnable(HandsOnRunnable)`` because
    DSS loads the runnable by that name. Subclasses implement :meth:`execute`
    instead of :meth:`run`; :meth:`run` enforces that the macro is launched
    from the admin project and then delegates to :meth:`execute`.

    Subclasses that report progress override :meth:`get_progress_target`.
    """

    ADMIN_PROJECT_KEY = "ADMINV4"

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config or {}
        self.plugin_config = plugin_config or {}
        self.client = dataiku.api_client()

    @property
    def admin_project_key(self):
        return self.ADMIN_PROJECT_KEY

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
