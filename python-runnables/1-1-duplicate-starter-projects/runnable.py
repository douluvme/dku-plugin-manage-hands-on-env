# Duplicate the selected starter projects once per workshop user (instructor user99 first).
import traceback
from collections import OrderedDict

from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.projects import duplicate_project, existing_project_keys, suffixed_key
from managehandsonenv.results import grouped_lines, html_key, render_result
from managehandsonenv.users import get_user_folder, iter_user_nums, user_id


class MyRunnable(HandsOnRunnable):
    def __init__(self, project_key, config, plugin_config):
        super().__init__(project_key, config, plugin_config)
        self.user_count = int(self.config["user_count"])
        self.dup_project_keys = self._get_project_keys()
        self.total_progress_target = len(self.dup_project_keys) * (self.user_count + 1)
        print("Progress target = {}".format(self.total_progress_target))

    def _get_project_keys(self):
        if self.config["key_select_method"] == "from_list":
            return list(self.config["project_keys_list"])
        return list(self.config["project_keys_input"])

    def get_progress_target(self):
        return (self.total_progress_target, 'NONE')

    def execute(self, progress_callback):
        client = self.client
        print("Number of users = {}".format(self.user_count + 1))

        existing = existing_project_keys(client)
        created = OrderedDict()
        skipped = []
        failures = []
        total_dup_count = 0
        progress = 1

        for user_num in iter_user_nums(self.user_count):
            user = user_id(user_num)
            created[user] = []

            try:
                user_folder = get_user_folder(client, user, create=True, sandbox_folder=self.settings.sandbox_folder)
            except Exception as e:
                print("Failed to get/create folder for {}: {}".format(user, e))
                traceback.print_exc()
                failures.append((user, "folder: {}".format(e)))
                progress += len(self.dup_project_keys)
                progress_callback(min(progress, self.total_progress_target))
                continue

            for project in self.dup_project_keys:
                progress_callback(progress)
                progress += 1

                target_key = suffixed_key(project, user_num)
                if target_key in existing:
                    print("Skip {} (already exists)".format(target_key))
                    skipped.append(target_key)
                    continue

                try:
                    duplicate_project(client, project, target_key, user_folder)
                except Exception as e:
                    print("{} duplication failed: {}".format(target_key, e))
                    traceback.print_exc()
                    failures.append((target_key, str(e)))
                    continue

                existing.add(target_key)
                total_dup_count += 1
                created[user].append(html_key(target_key))

        return render_result(
            "Successfully duplicated {} project(s)".format(total_dup_count),
            grouped_lines(created),
            skipped=skipped,
            failures=failures,
        )
