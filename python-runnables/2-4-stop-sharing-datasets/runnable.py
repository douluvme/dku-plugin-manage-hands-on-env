# This file is the actual code for the Python runnable 2-4-stop-sharing-datasets
from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    """Stop sharing READONLY.credit_score with every project except the KO4EVAL*
    starters and DEMO_KO_CARDFRAUD."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        client = self.client

        project = client.get_project("READONLY")

        settings = project.get_settings()
        objects = settings.get_raw()['exposedObjects']['objects']
        rules = next((obj for obj in objects if obj['localName'] == 'credit_score'), None)['rules']

        index_list = []

        for x in range(0, len(rules)):
            if rules[x]['targetProject'].startswith('KO4EVAL') or rules[x]['targetProject'] == 'DEMO_KO_CARDFRAUD':
                pass
            else:
                print(f"Target project : {rules[x]['targetProject']}")
                index_list.append(x)

        for index in sorted(index_list, reverse=True):
            del rules[index]

        settings.save()

        print(f"Stopped sharing {len(index_list)} shared project(s)")

        progress_callback(1)

        return f"Stopped sharing {len(index_list)} shared project(s)"
