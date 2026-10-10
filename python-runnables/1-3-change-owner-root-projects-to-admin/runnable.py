# Change the owner of every project directly in the sandbox folder to admin.
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.projects import set_project_owner
from managehandsonenv.results import failures_section, key_lines


class MyRunnable(HandsOnRunnable):
    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        sandbox_folder = self.client.get_project_folder(self.settings.sandbox_folder)

        updated = []
        failures = []
        for project_key in sandbox_folder.list_project_keys():
            print("Project to update : {}".format(project_key))
            if set_project_owner(self.client, project_key, "admin"):
                updated.append(project_key)
            else:
                failures.append((project_key, "update failed"))

        progress_callback(1)

        return "Successfully changed owner of {} project(s) to admin</br></br>{}{}".format(
            len(updated), key_lines(updated), failures_section(failures)
        )
