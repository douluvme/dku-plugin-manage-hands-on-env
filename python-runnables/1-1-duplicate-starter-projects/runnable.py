# This file is the actual code for the Python runnable 1-1-duplicate-starter-projects
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.users import iter_user_nums, user_id, get_user_folder
from managehandsonenv.projects import suffixed_key, project_exists, duplicate_project
from managehandsonenv.results import html_key, user_heading, render_result
import traceback


class MyRunnable(HandsOnRunnable):
    """Duplicate the selected starter projects once per user (user99 + user01..NN)."""

    def __init__(self, project_key, config, plugin_config):
        super().__init__(project_key, config, plugin_config)
        self.number_of_users = int(config["user_count"]) + 1
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
        config = self.config
        client = self.client

        print(f"Number of users = {self.number_of_users}")

        total_dup_count = 0
        skipped = []
        failures = []
        result_string = ""
        progress = 1

        for user_num in iter_user_nums(config["user_count"]):
            user = user_id(user_num)
            result_string += user_heading(user)

            try:
                user_folder = get_user_folder(client, user, create=True)
            except Exception as e:
                print(f"Failed to get/create folder for {user}: {e}")
                traceback.print_exc()
                failures.append((user, f"folder: {e}"))
                progress += len(self.dup_project_keys)
                progress_callback(min(progress, self.total_progress_target))
                continue

            for project in self.dup_project_keys:
                progress_callback(progress)
                progress += 1

                target_key = suffixed_key(project, user_num)

                if project_exists(client, target_key):
                    print(f"Skip {target_key} (already exists)")
                    skipped.append(target_key)
                    continue

                try:
                    result = duplicate_project(client, project, target_key, user_folder)
                except Exception as e:
                    print(f"{target_key} duplication failed: {e}")
                    traceback.print_exc()
                    failures.append((target_key, str(e)))
                    continue

                if not result:
                    print(f"{target_key} duplication returned empty result")
                    failures.append((target_key, "empty result"))
                    continue

                total_dup_count += 1
                result_string += f" {html_key(target_key)}"

        return render_result(
            f"Successfully duplicated {total_dup_count} project(s)",
            result_string,
            skipped=skipped,
            failures=failures,
        )
