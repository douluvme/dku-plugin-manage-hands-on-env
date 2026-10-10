# This file is the actual code for the Python runnable 1-3-change-owner-root-projects-to-admin
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.common_functions import *


class MyRunnable(HandsOnRunnable):
    """Set the owner of every project directly under the SANDBOX folder to admin."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        client = self.client
        total_update_count = 0
        result_string = ""

        sandbox_folder = client.get_project_folder('SANDBOX')
        project_list = sandbox_folder.list_project_keys()

        for project_id in project_list:
            try:
                print(f"Update {project_id}")
                total_update_count += set_project_owner(client, project_id, 'admin')
                result_string = f"{result_string}&lt;{project_id}&gt;</br>"
            except Exception as e:
                print(f"{project_id} update failed: {e}")

        progress_callback(1)

        return_msg = f"Successfully changed owner of {total_update_count} project(s) to admin</br></br>{result_string}"
        return return_msg
