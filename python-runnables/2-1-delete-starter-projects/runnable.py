# This file is the actual code for the Python runnable 2-1-delete-starter-projects
from managehandsonenv import base
from managehandsonenv.users import (
    SANDBOX_FOLDER, iter_user_nums, user_id, get_user_folder, list_user_folders, walk_folder_tree,
)
from managehandsonenv.projects import suffixed_key, project_exists, delete_project
from managehandsonenv.results import html_key, user_heading, render_result, render_failures
import time
import traceback


class MyRunnable(base.HandsOnRunnable):
    """Delete hands-on projects: by user number, everything under every user folder,
    or everything in the SANDBOX (or root) folder. Dry-run unless delete_TF is set."""

    def __init__(self, project_key, config, plugin_config):
        super().__init__(project_key, config, plugin_config)
        client = self.client

        if config["delete_type"] == 'user_num':
            self.total_progress_target = len(self._get_project_keys()) * (int(config["user_count"]) + 1)
        elif config["delete_type"] == 'sandbox':
            self.total_progress_target = len(client.get_project_folder(SANDBOX_FOLDER).list_project_keys())
        elif config["delete_type"] == 'all_user_folders':
            total = 0
            for user_folder in list_user_folders(client):
                for _folder, _depth, project_keys in walk_folder_tree(user_folder):
                    total += len(project_keys) + 1

            print(f"progress target = {total}")
            self.total_progress_target = max(total, 1)
        else:
            self.total_progress_target = len(client.get_root_project_folder().list_project_keys())

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
        delete_type = config["delete_type"]
        delete_TF = config["delete_TF"]
        total_delete_count = 0
        total_folder_count = 0
        result_string = ""
        failures = []
        kept_folders = set()
        progress = 1

        if delete_type == 'user_num':
            print(f"Number of users = {int(config['user_count']) + 1}")
            del_project_keys = self._get_project_keys()

            for user_num in iter_user_nums(config["user_count"]):
                user = user_id(user_num)
                result_string += user_heading(user)

                user_folder = get_user_folder(client, user, create=False)

                for project in del_project_keys:
                    progress_callback(progress)
                    progress += 1

                    target_key = suffixed_key(project, user_num)

                    if not project_exists(client, target_key):
                        continue

                    if delete_TF and not delete_project(client, target_key):
                        failures.append((target_key, "delete failed, see log"))
                        continue

                    total_delete_count += 1
                    result_string += f" {html_key(target_key)}"

                if user_folder is None:
                    print("Skip deleting user folder")
                elif delete_TF:
                    print(f"Folder to delete = {user_folder.get_name()}")
                    try:
                        user_folder.delete()
                        total_folder_count += 1
                    except Exception as e:
                        print(f"Failed deleting folder {user_folder.get_name()}: {e}")
                        traceback.print_exc()
                        failures.append((user_folder.get_name(), str(e)))

        elif delete_type == 'all_user_folders':
            keep_project_keys = set(config["projects_to_keep"])
            keep_project_keys.add(self.project_key)

            user_folders = list_user_folders(client)
            print(f"Found {len(user_folders)} user folder(s)")

            for user_folder in user_folders:
                result_string += user_heading(user_folder.get_name())

                for folder, depth, project_keys in walk_folder_tree(user_folder):
                    folder_name = folder.get_name()
                    indent = "  " * depth
                    folder_clean = True

                    for del_project_id in project_keys:
                        progress_callback(progress)
                        progress += 1

                        if del_project_id in keep_project_keys:
                            print(f"{indent}Keep {del_project_id}")
                            folder_clean = False
                            continue

                        if delete_TF and not delete_project(client, del_project_id):
                            failures.append((del_project_id, "delete failed, see log"))
                            folder_clean = False
                            continue

                        total_delete_count += 1
                        result_string += f" {html_key(del_project_id)}"

                    progress_callback(progress)
                    progress += 1

                    if not folder_clean:
                        print(f"{indent}Keep folder {folder_name} (not empty)")
                        kept_folders.add(folder_name)
                        continue

                    # Keep this parent only if a child was KEPT (in kept_folders).
                    # Test membership, NOT list_child_folders() presence — presence
                    # differs between dry-run and real run, membership does not.
                    # This is what keeps the dry-run and real-run counts identical.
                    if any(c.get_name() in kept_folders for c in folder.list_child_folders()):
                        print(f"{indent}Keep folder {folder_name} (child folder kept)")
                        kept_folders.add(folder_name)
                        continue

                    if not delete_TF:
                        total_folder_count += 1
                        result_string += f" <i>[+{folder_name}]</i>"
                        continue

                    try:
                        folder.delete()
                        print(f"{indent}Deleted folder {folder_name}")
                        total_folder_count += 1
                        result_string += f" <i>[+{folder_name}]</i>"
                    except Exception as e:
                        print(f"{indent}Failed deleting folder {folder_name}: {e}")
                        traceback.print_exc()
                        failures.append((folder_name, str(e)))
                        kept_folders.add(folder_name)

        else:
            keep_project_keys = list(config["projects_to_keep"])

            # never delete the project this macro is running from
            if self.project_key not in keep_project_keys:
                keep_project_keys.append(self.project_key)

            for project_key in keep_project_keys:
                print(f"Keep {project_key}")

            if delete_type == 'sandbox':
                folder_to_clean = client.get_project_folder(SANDBOX_FOLDER)
            else:
                folder_to_clean = client.get_root_project_folder()

            for del_project_id in folder_to_clean.list_project_keys():
                progress_callback(progress)
                progress += 1

                if del_project_id in keep_project_keys:  # 삭제하지 않을 프로젝트명
                    print(f"Keep {del_project_id}")
                    continue

                if not delete_TF:
                    total_delete_count += 1
                    result_string += f"{html_key(del_project_id)}<br/>"
                    time.sleep(0.07)
                    continue

                if not delete_project(client, del_project_id):
                    failures.append((del_project_id, "delete failed, see log"))
                    continue

                total_delete_count += 1
                result_string += f"{html_key(del_project_id)}<br/>"

        if delete_TF:
            return_msg = render_result(f"Successfully deleted {total_delete_count} project(s)", result_string)
        else:
            return_msg = render_result(f"Identified {total_delete_count} project(s) to delete", f"<br/>{result_string}")

        verb = "Deleted" if delete_TF else "Identified"
        return_msg += f"<h4>{verb} {total_folder_count} user folder(s)</h4>"
        return_msg += render_failures(failures)

        return return_msg
