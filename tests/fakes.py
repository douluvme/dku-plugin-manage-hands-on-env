"""In-memory stand-ins for the handful of dataikuapi objects the library uses.

Every mutating call is appended to ``FakeClient.calls`` as a tuple, so tests can
assert exactly what was deleted, duplicated or re-owned. Keys or folder paths
listed in ``FakeClient.fail`` make the corresponding operation raise.
"""
import copy
from typing import Dict, Iterable, List, Optional, Tuple


class FakeFolderSettings:
    def __init__(self, folder):
        self.folder = folder
        self.owner = folder.owner

    def set_owner(self, owner):
        self.owner = owner

    def save(self):
        self.folder.owner = self.owner
        self.folder.client.calls.append(("save_folder_settings", self.folder.path, self.owner))


class FakeFolder:
    def __init__(self, client, name, parent=None):
        self.client = client
        self.name = name
        self.parent = parent
        self.children: List["FakeFolder"] = []
        self.project_keys: List[str] = []
        self.owner: Optional[str] = None

    @property
    def path(self) -> str:
        if self.parent is None or self.parent.parent is None:
            return self.name
        return self.parent.path + "/" + self.name

    def get_name(self):
        return self.name

    def list_child_folders(self):
        return list(self.children)

    def list_project_keys(self):
        return list(self.project_keys)

    def create_sub_folder(self, name):
        child = FakeFolder(self.client, name, self)
        self.children.append(child)
        self.client.calls.append(("create_sub_folder", self.path, name))
        return child

    def get_settings(self):
        return FakeFolderSettings(self)

    def delete(self):
        self.client.calls.append(("delete_folder", self.path))
        if self.path in self.client.fail:
            raise RuntimeError("cannot delete folder {}".format(self.path))
        # like DSS, move remaining content to the parent folder
        for key in self.project_keys:
            self.client.projects[key].folder = self.parent
            self.parent.project_keys.append(key)
        for child in self.children:
            child.parent = self.parent
            self.parent.children.append(child)
        self.parent.children.remove(self)

    def __repr__(self):
        return "FakeFolder({!r})".format(self.path)


class FakeProject:
    def __init__(self, client, key, folder=None, label=None):
        self.client = client
        self.key = key
        self.folder = folder
        self.permissions = {"owner": "admin", "permissions": []}
        self.metadata = {"label": label or key, "tags": []}

    def _check(self):
        if self.key not in self.client.projects:
            raise RuntimeError("Project not found: {}".format(self.key))
        if self.key in self.client.fail:
            raise RuntimeError("API error on project {}".format(self.key))

    def get_permissions(self):
        self._check()
        return copy.deepcopy(self.permissions)

    def set_permissions(self, permissions):
        self._check()
        self.permissions = copy.deepcopy(permissions)
        self.client.calls.append(("set_permissions", self.key, permissions.get("owner")))

    def get_metadata(self):
        self._check()
        return copy.deepcopy(self.metadata)

    def set_metadata(self, metadata):
        self._check()
        self.metadata = copy.deepcopy(metadata)
        self.client.calls.append(("set_metadata", self.key, list(metadata.get("tags", []))))

    def get_project_folder(self):
        self._check()
        return self.folder

    def delete(self, **kwargs):
        self.client.calls.append(("delete_project", self.key))
        self._check()
        self.client.remove_project(self.key)

    def duplicate(self, target_project_key, target_project_name, duplication_mode="FULL",
                  target_project_folder=None, export_saved_models=False, **kwargs):
        self._check()
        if target_project_key in self.client.projects:
            raise RuntimeError("Project {} already exists".format(target_project_key))
        self.client.add_project(target_project_key, target_project_folder or self.client.root, label=target_project_name)
        self.client.calls.append(("duplicate", self.key, target_project_key))

    def __repr__(self):
        return "FakeProject({!r})".format(self.key)


class FakeClient:
    def __init__(self):
        self.root = FakeFolder(self, "ROOT")
        self.projects: Dict[str, FakeProject] = {}
        self.calls: List[Tuple] = []
        self.fail = set()

    # --- dataikuapi surface -------------------------------------------------
    def get_root_project_folder(self):
        return self.root

    def get_project_folder(self, ref):
        for folder in self.walk(self.root):
            if folder.name == ref or folder.path == ref:
                return folder
        raise RuntimeError("Project folder not found: {}".format(ref))

    def list_project_keys(self):
        return list(self.projects)

    def get_project(self, key):
        # DSS hands back a handle even for a missing project; operations on it fail
        return self.projects.get(key) or FakeProject(self, key)

    # --- test helpers -------------------------------------------------------
    def walk(self, folder):
        yield folder
        for child in folder.children:
            for item in self.walk(child):
                yield item

    def add_folder(self, path: str) -> FakeFolder:
        """Create (or fetch) the folder at ``"SANDBOX/user01/work"``, creating parents as needed."""
        folder = self.root
        for name in path.split("/"):
            child = next((c for c in folder.children if c.name == name), None)
            if child is None:
                child = FakeFolder(self, name, folder)
                folder.children.append(child)
            folder = child
        return folder

    def add_project(self, key: str, folder=None, label=None) -> FakeProject:
        folder = folder or self.root
        if isinstance(folder, str):
            folder = self.add_folder(folder)
        project = FakeProject(self, key, folder, label)
        self.projects[key] = project
        folder.project_keys.append(key)
        return project

    def remove_project(self, key: str):
        project = self.projects.pop(key)
        if project.folder is not None:
            project.folder.project_keys.remove(key)

    def build(self, tree: Dict[str, Iterable[str]]):
        """``{"SANDBOX/user01": ["A", "B"], "ROOT": ["ADMINV4"]}`` -> folders and projects."""
        for path, keys in tree.items():
            folder = self.root if path == "ROOT" else self.add_folder(path)
            for key in keys:
                self.add_project(key, folder)
        return self

    def deleted_projects(self) -> List[str]:
        return [call[1] for call in self.calls if call[0] == "delete_project"]

    def deleted_folders(self) -> List[str]:
        return [call[1] for call in self.calls if call[0] == "delete_folder"]
