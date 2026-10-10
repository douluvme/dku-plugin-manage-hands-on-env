# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.base import HandsOnRunnable

#: Used when the target_projects_to_keep param is left empty.
DEFAULT_TARGETS_TO_KEEP = ("KO4EVAL", "DEMO_KO_CARDFRAUD")


class MyRunnable(HandsOnRunnable):
    """Remove the sharing rules of the shared dataset, except for the target projects to keep.

    Each entry of ``target_projects_to_keep`` is a prefix: a rule is kept when its
    target project key starts with one of the entries, so ``KO4EVAL`` also keeps
    ``KO4EVAL_01``, ``KO4EVAL_99`` and so on.
    """

    def get_progress_target(self):
        return (1, 'NONE')

    def _targets_to_keep(self):
        entries = self.config.get("target_projects_to_keep") or []
        entries = tuple(e.strip() for e in entries if e and e.strip())
        return entries or DEFAULT_TARGETS_TO_KEEP

    def execute(self, progress_callback):
        client = self.client
        readonly_key = self.settings.readonly_project_key
        dataset_name = self.settings.shared_dataset_name
        keep_prefixes = self._targets_to_keep()
        print(f"Keep sharing with target projects starting with: {', '.join(keep_prefixes)}")

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
            if target.startswith(keep_prefixes):
                continue
            print(f"Target project : {target}")
            index_list.append(x)

        for index in sorted(index_list, reverse=True):
            del rules[index]

        settings.save()

        print(f"Stopped sharing {len(index_list)} shared project(s)")

        progress_callback(1)

        return f"Stopped sharing {dataset_name} with {len(index_list)} project(s)"
