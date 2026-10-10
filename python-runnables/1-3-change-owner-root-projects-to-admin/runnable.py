# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.projects import set_project_owner
from managehandsonenv.results import key_tag


class MyRunnable(HandsOnRunnable):
    """Set the owner of every project directly under the sandbox folder to admin."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        client = self.client
        total_update_count = 0
        result_string = ""

        sandbox_folder = client.get_project_folder(self.settings.sandbox_folder)
        project_list = sandbox_folder.list_project_keys()

        for project_id in project_list:
            if set_project_owner(client, project_id, 'admin'):
                total_update_count += 1
                result_string = f"{result_string}{key_tag(project_id)}</br>"

        progress_callback(1)

        return f"Successfully changed owner of {total_update_count} project(s) to admin</br></br>{result_string}"
