# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    """Remove the sharing rules of the shared dataset, except for the projects to keep."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        client = self.client
        readonly_key = self.settings.readonly_project_key
        dataset_name = self.settings.shared_dataset_name

        project = client.get_project(readonly_key)

        settings = project.get_settings()
        objects = settings.get_raw()['exposedObjects']['objects']
        exposed = next((obj for obj in objects if obj['localName'] == dataset_name), None)
        if exposed is None:
            raise RuntimeError(f"Dataset {dataset_name} is not exposed by project {readonly_key}")
        rules = exposed['rules']

        index_list = []

        for x in range(len(rules)):
            target = rules[x]['targetProject']
            if target.startswith('KO4EVAL') or target == 'DEMO_KO_CARDFRAUD':
                continue
            print(f"Target project : {target}")
            index_list.append(x)

        for index in sorted(index_list, reverse=True):
            del rules[index]

        settings.save()

        print(f"Stopped sharing {len(index_list)} shared project(s)")

        progress_callback(1)

        return f"Stopped sharing {len(index_list)} shared project(s)"
