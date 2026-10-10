# Delete starter projects (by user number, per user folder, or a whole folder), with a dry-run mode.
from collections import OrderedDict

from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.deletion import PROJECT, apply, build_plan
from managehandsonenv.results import failures_section, folder_marker, grouped_lines, heading, html_key, key_lines


class MyRunnable(HandsOnRunnable):
    def __init__(self, project_key, config, plugin_config):
        super().__init__(project_key, config, plugin_config)
        self.plan = build_plan(self.client, self.settings, self.config, self.project_key)
        self.targets = self.plan.targets()
        print("Progress target = {}".format(len(self.targets)))

    def get_progress_target(self):
        return (max(len(self.targets), 1), 'NONE')

    def execute(self, progress_callback):
        dry_run = not self.config.get("delete_TF", False)
        result = apply(self.targets, self.client, dry_run=dry_run, progress_callback=progress_callback)

        if dry_run:
            title = "Identified {} project(s) to delete".format(len(result.projects))
            verb = "Identified"
        else:
            title = "Successfully deleted {} project(s)".format(len(result.projects))
            verb = "Deleted"

        return (
            heading(title)
            + self._render_body(result)
            + heading("{} {} user folder(s)".format(verb, len(result.folders)))
            + failures_section(result.failures)
        )

    def _render_body(self, result):
        if not any(t.group for t in self.targets):  # whole-folder modes: flat listing
            return key_lines(t.key for t in result.projects)

        # one line per user folder, in plan order, even when nothing in it is deleted
        groups = OrderedDict((t.group, []) for t in self.targets)
        for target in result.done:
            groups[target.group].append(html_key(target.key) if target.kind == PROJECT else folder_marker(target.key))
        return grouped_lines(groups)
