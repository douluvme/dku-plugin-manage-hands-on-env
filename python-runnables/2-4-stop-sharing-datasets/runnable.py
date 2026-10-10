# Stop sharing the shared dataset of the read-only project with every project not in the keep list.
from managehandsonenv.base import HandsOnRunnable

DEFAULT_TARGETS_TO_KEEP = ["KO4EVAL", "DEMO_KO_CARDFRAUD"]


class MyRunnable(HandsOnRunnable):
    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        readonly_key = self.settings.readonly_project_key
        dataset_name = self.settings.shared_dataset_name
        keep_prefixes = self.config.get("target_projects_to_keep")
        if keep_prefixes is None:  # parameter absent (older saved config): historical behaviour
            keep_prefixes = DEFAULT_TARGETS_TO_KEEP
        keep_prefixes = [p for p in keep_prefixes if p]

        project = self.client.get_project(readonly_key)
        settings = project.get_settings()
        objects = settings.get_raw()['exposedObjects']['objects']
        exposed = next((obj for obj in objects if obj['localName'] == dataset_name), None)
        if exposed is None:
            raise RuntimeError("Dataset {} is not exposed by project {}".format(dataset_name, readonly_key))
        rules = exposed['rules']

        index_list = []
        for index, rule in enumerate(rules):
            target = rule['targetProject']
            if any(target.startswith(prefix) for prefix in keep_prefixes):
                print("Keep sharing with {}".format(target))
            else:
                print("Target project : {}".format(target))
                index_list.append(index)

        for index in sorted(index_list, reverse=True):
            del rules[index]

        settings.save()

        print("Stopped sharing {} shared project(s)".format(len(index_list)))
        progress_callback(1)

        return "Stopped sharing {} shared project(s)".format(len(index_list))
