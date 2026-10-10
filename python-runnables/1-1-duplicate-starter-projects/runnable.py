# This file is the actual code for the Python runnable manage-starter-project
import traceback

from managehandsonenv import base
from managehandsonenv.projects import duplicate_project, project_exists, suffixed_key
from managehandsonenv.results import key_tag, render_result
from managehandsonenv.users import get_user_folder, iter_user_nums, user_id


class MyRunnable(base.HandsOnRunnable):
    """Duplicate the selected starter projects once per user (instructor + attendees)."""

    def __init__(self, project_key, config, plugin_config):
        super().__init__(project_key, config, plugin_config)
        self.user_count = int(self.config["user_count"])
        self.number_of_users = self.user_count + 1
        self.dup_project_keys = self._get_project_keys()
        self.total_progress_target = len(self.dup_project_keys) * self.number_of_users
        print(f"Progress target = {self.total_progress_target}")

    def _get_project_keys(self):
        config = self.config
        if config["key_select_method"] == "from_list":
            return config["project_keys_list"]
        return config["project_keys_input"]

    def get_progress_target(self):
        return (self.total_progress_target, 'NONE')

    def execute(self, progress_callback):
        client = self.client
        sandbox_folder = self.settings.sandbox_folder

        print(f"Number of users = {self.number_of_users}")

        total_dup_count = 0
        skipped = []
        failures = []
        result_string = ""
        progress = 1

        for num in iter_user_nums(self.user_count):
            login = user_id(num)
            result_string = f"{result_string}<br/><b>{login}</b> :"

            try:
                user_folder = get_user_folder(client, login, sandbox_folder, create=True)
            except Exception as e:
                print(f"Failed to get/create folder for {login}: {e}")
                traceback.print_exc()
                failures.append((login, f"folder: {e}"))
                progress += len(self.dup_project_keys)
                progress_callback(min(progress, self.total_progress_target))
                continue

            for project in self.dup_project_keys:
                progress_callback(progress)
                progress += 1

                target_key = suffixed_key(project, num)

                if project_exists(client, target_key):
                    print(f"Skip {target_key} (already exists)")
                    skipped.append(target_key)
                    continue

                try:
                    duplicate_project(client, project, target_key, user_folder)
                except Exception as e:
                    print(f"{target_key} duplication failed: {e}")
                    traceback.print_exc()
                    failures.append((target_key, str(e)))
                    continue

                total_dup_count += 1
                result_string = f"{result_string} {key_tag(target_key)}"

        return render_result(
            f"Successfully duplicated {total_dup_count} project(s)",
            result_string,
            skipped=skipped,
            failures=failures,
        )
