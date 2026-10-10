# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    """Remove the sharing rules of the shared dataset, except for the projects to keep."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        client = self.client

        project = client.get_project("READONLY")

        settings = project.get_settings()
        objects = settings.get_raw()['exposedObjects']['objects']
        exposed = next((obj for obj in objects if obj['localName'] == 'credit_score'), None)
        if exposed is None:
            raise RuntimeError("Dataset credit_score is not exposed by project READONLY")
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
