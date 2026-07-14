# This file is the actual code for the Python runnable manage-starter-project
from dataiku.runnables import Runnable
import dataiku
from managehandsonenv.common_functions import *
import time
import traceback


class MyRunnable(Runnable):
    def __init__(self, project_key, config, plugin_config):
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        client = dataiku.api_client()
        self.client = client

        if config["delete_type"] == 'user_num':
            project_keys = (config["project_keys_list"]
                            if config["key_select_method"] == "from_list"
                            else config["project_keys_input"])
            self.total_progress_target = len(project_keys) * (int(config["user_count"]) + 1)
        elif config["delete_type"] == 'sandbox':
            self.total_progress_target = len(client.get_project_folder('SANDBOX').list_project_keys())
        elif config["delete_type"] == 'all_user_folders':
            total = 0
            for user_folder in list_user_folders(client):
                for _folder, _depth, project_keys, _child_folders in walk_folder_tree(user_folder):
                    total += len(project_keys) + 1
                    
            print(f"progress target = {total}")
            self.total_progress_target = max(total, 1)
        else:
            self.total_progress_target = len(client.get_root_project_folder().list_project_keys())

        print(f"Progress target = {self.total_progress_target}")

    def get_progress_target(self):
        return (self.total_progress_target, 'NONE')

    def run(self, progress_callback):
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

        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(5)
            return None

        if delete_type == 'user_num':
            number_of_users = int(config["user_count"]) + 1
            print(f"Number of users = {number_of_users}")
            del_project_keys = (config["project_keys_list"]
                                if config["key_select_method"] == "from_list"
                                else config["project_keys_input"])

            for x in range(number_of_users):
                user_num = '99' if x == 0 else str(x).zfill(2)
                sep = "<br/>" if result_string else ""
                result_string = f"{result_string}{sep}<b>user{user_num}</b> :"

                user_folder = get_user_folder_by_id(client, 'user' + user_num, create_if_not_exist_TF=False)

                for project in del_project_keys:
                    progress_callback(progress)
                    progress += 1

                    if not project_exists(client, f"{project}_{user_num}"):
                        continue

                    if delete_TF:
                        try:
                            result = delete_project_by_num(client, project, user_num)
                        except Exception as e:
                            print(f"{project}_{user_num} delete failed: {e}")
                            traceback.print_exc()
                            failures.append((f"{project}_{user_num}", str(e)))
                            continue

                        if result != 1:
                            print(f"{project}_{user_num} delete returned {result}")
                            failures.append((f"{project}_{user_num}", f"returned {result}"))
                            continue

                    total_delete_count += 1
                    result_string = f"{result_string} &lt;{project}_{user_num}&gt;"

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
                sep = "<br/>" if result_string else ""
                result_string = f"{result_string}{sep}<b>{user_folder.get_name()}</b> :"

                for folder, depth, project_keys, child_folders in walk_folder_tree(user_folder):
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

                        if not delete_TF:
                            total_delete_count += 1
                            result_string = f"{result_string} &lt;{del_project_id}&gt;"
                            continue

                        print(f"{indent}Delete {del_project_id}")
                        try:
                            client.get_project(del_project_id).delete(
                                clear_managed_datasets=True,
                                clear_job_and_scenario_logs=True,
                            )
                        except Exception as e:
                            print(f"{indent}{del_project_id} delete failed: {e}")
                            traceback.print_exc()
                            failures.append((del_project_id, str(e)))
                            folder_clean = False
                            continue

                        total_delete_count += 1
                        result_string = f"{result_string} &lt;{del_project_id}&gt;"

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
                    # Reuse child_folders from the walk instead of re-listing here:
                    # by this point some children may already be deleted, and
                    # re-fetching them by id would 403/404.
                    if any(c.get_name() in kept_folders for c in child_folders):
                        print(f"{indent}Keep folder {folder_name} (child folder kept)")
                        kept_folders.add(folder_name)
                        continue

                    if not delete_TF:
                        total_folder_count += 1
                        result_string = f"{result_string} <i>[+{folder_name}]</i>"
                        continue

                    try:
                        folder.delete()
                        print(f"{indent}Deleted folder {folder_name}")
                        total_folder_count += 1
                        result_string = f"{result_string} <i>[+{folder_name}]</i>"
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
                folder_to_clean = client.get_project_folder('SANDBOX')
            else:
                folder_to_clean = client.get_root_project_folder()

            del_project_list = folder_to_clean.list_project_keys()

            for del_project_id in del_project_list:
                progress_callback(progress)
                progress += 1

                if del_project_id in keep_project_keys:  # 삭제하지 않을 프로젝트명
                    print(f"Keep {del_project_id}")
                    continue

                if not delete_TF:
                    total_delete_count += 1
                    result_string = f"{result_string}&lt;{del_project_id}&gt;<br/>"
                    time.sleep(0.07)
                    continue

                print(f"Delete {del_project_id}")
                try:
                    client.get_project(del_project_id).delete(
                        clear_managed_datasets=True,
                        clear_job_and_scenario_logs=True,
                    )
                except Exception as e:
                    print(f"{del_project_id} delete failed: {e}")
                    traceback.print_exc()
                    failures.append((del_project_id, str(e)))
                    continue

                total_delete_count += 1
                result_string = f"{result_string}&lt;{del_project_id}&gt;<br/>"

        if delete_TF:
            return_msg = f"<h4>Successfully deleted {total_delete_count} project(s)</h4>{result_string}"
        else:
            return_msg = f"<h4>Identified {total_delete_count} project(s) to delete</h4>{result_string}"

        if total_folder_count:
            verb = "Deleted" if delete_TF else "Identified"
            return_msg += f"<h4>{verb} {total_folder_count} user folder(s)</h4>"

        if failures:
            rows = "".join(f"<li>&lt;{k}&gt; — {reason}</li>" for k, reason in failures)
            return_msg += f"<h4>{len(failures)} failure(s)</h4><ul>{rows}</ul>"

        return return_msg