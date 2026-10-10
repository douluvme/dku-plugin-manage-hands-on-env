# This file is the actual code for the Python runnable 1-3-change-owner-root-projects-to-admin
from managehandsonenv import base
from managehandsonenv.users import SANDBOX_FOLDER
from managehandsonenv.projects import set_project_owner
from managehandsonenv.results import html_key, render_failures


class MyRunnable(base.HandsOnRunnable):
    """Set the owner of every project directly under the SANDBOX folder to admin."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        client = self.client
        updated = []
        failures = []

        sandbox_folder = client.get_project_folder(SANDBOX_FOLDER)

        for project_id in sandbox_folder.list_project_keys():
            print(f"Update {project_id}")
            if set_project_owner(client, project_id, 'admin'):
                updated.append(project_id)
            else:
                failures.append((project_id, "set owner failed, see log"))

        progress_callback(1)

        result_string = "".join(f"{html_key(k)}</br>" for k in updated)
        return (f"Successfully changed owner of {len(updated)} project(s) to admin</br></br>{result_string}"
                + render_failures(failures))
