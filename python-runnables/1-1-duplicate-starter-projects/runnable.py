# This file is the actual code for the Python runnable manage-starter-project
from dataiku.runnables import Runnable
import dataiku
from managehandsonenv.common_functions import *
import time
import traceback


class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        self.client = dataiku.api_client()
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

    def run(self, progress_callback):
        config = self.config
        client = self.client
        overwrite_TF = config.get("overwrite_TF", False)

        if self.project_key != 'ADMINV4':
            raise Exception("This macro can be run only from the ADMINV4 admin project")

        print(f"Number of users = {self.number_of_users}")

        total_dup_count = 0
        skipped = []
        failures = []
        result_string = ""
        progress = 1

        for x in range(self.number_of_users):
            user_num = '99' if x == 0 else str(x).zfill(2)
            user_id = 'user' + user_num
            result_string = f"{result_string}<br/><b>{user_id}</b> :"

            try:
                user_folder = get_user_folder_by_id(client, user_id, create_if_not_exist_TF=True)
            except Exception as e:
                print(f"Failed to get/create folder for {user_id}: {e}")
                traceback.print_exc()
                failures.append((user_id, f"folder: {e}"))
                progress += len(self.dup_project_keys)
                progress_callback(min(progress, self.total_progress_target))
                continue

            for project in self.dup_project_keys:
                progress_callback(progress)
                progress += 1

                target_key = f"{project}_{user_num}"

                if project_exists(client, target_key):
                    print(f"Skip {target_key} (already exists)")
                    skipped.append(target_key)
                    continue

                try:
                    result = duplicate_project_by_num(
                        client, project, user_num, user_folder
                    )
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
                result_string = f"{result_string} &lt;{target_key}&gt;"

        return_msg = f"<h4>Successfully duplicated {total_dup_count} project(s)</h4>{result_string}"

        if skipped:
            rows = "".join(f"<li>&lt;{k}&gt;</li>" for k in skipped)
            return_msg += f"<h4>{len(skipped)} skipped (already exist)</h4><ul>{rows}</ul>"

        if failures:
            rows = "".join(f"<li>&lt;{k}&gt; — {reason}</li>" for k, reason in failures)
            return_msg += f"<h4>{len(failures)} failure(s)</h4><ul>{rows}</ul>"

        return return_msg