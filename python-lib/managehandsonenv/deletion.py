"""Delete plans for the "Delete Starter Projects" macro.

A :class:`DeletePlan` computes the ordered list of :class:`Target` items once
(``targets()``); ``len(targets)`` is the progress target. :func:`apply` then
either deletes them or, in dry-run mode, only reports them, so a dry run and a
real run always report the same set.

Three plans match the macro's ``delete_type``:

- ``user_num``: for each user (instructor 99, then 01..NN) the selected
  starter projects ``KEY_NN`` that exist, then the user's folder if it exists.
- ``all_user_folders``: every project in every ``userNN`` folder under the
  sandbox folder, deepest sub-folder first; a folder is deleted only when all
  its projects are deleted and every child folder is deleted too.
- ``sandbox`` / ``root_folder``: every project directly in that folder.

Projects in ``projects_to_keep`` and the project the macro runs from are never
deleted.
"""
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

from managehandsonenv.projects import delete_project, existing_project_keys, suffixed_key
from managehandsonenv.users import iter_user_nums, list_user_folders, user_id

PROJECT = "project"
FOLDER = "folder"


@dataclass(frozen=True)
class Target:
    """One item the plan will act on."""

    kind: str                            # PROJECT or FOLDER
    key: str                             # project key, or folder path such as "user01" / "user01/work"
    group: str = ""                      # user folder the item belongs to; "" for a flat listing
    depth: int = 0
    keep: bool = False                   # listed for completeness but never deleted
    depends_on: Tuple[str, ...] = ()     # folders only: keys that must be deleted before the folder
    handle: Any = field(default=None, compare=False, repr=False)  # folder object for FOLDER targets


@dataclass
class DeleteResult:
    """What :func:`apply` did (or, in dry-run mode, would do)."""

    dry_run: bool
    done: List[Target] = field(default_factory=list)       # deleted, or identified in dry-run mode
    kept: List[Target] = field(default_factory=list)
    failures: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def projects(self) -> List[Target]:
        return [t for t in self.done if t.kind == PROJECT]

    @property
    def folders(self) -> List[Target]:
        return [t for t in self.done if t.kind == FOLDER]

    def done_keys(self) -> Set[Tuple[str, str]]:
        """``{(kind, key)}`` of everything deleted/identified, for comparing runs."""
        return {(t.kind, t.key) for t in self.done}


class DeletePlan:
    """Base class: builds the target list from the macro config and the folder tree."""

    def __init__(self, client, settings, config: Dict[str, Any], running_project_key: str):
        self.client = client
        self.settings = settings
        self.config = config or {}
        self.running_project_key = running_project_key

    def keep_keys(self) -> Set[str]:
        """``projects_to_keep`` plus the project the macro runs from."""
        keys = set(self.config.get("projects_to_keep") or [])
        keys.add(self.running_project_key)
        return keys

    def targets(self) -> List[Target]:
        raise NotImplementedError


class ByUserNum(DeletePlan):
    """``delete_type == "user_num"``."""

    def project_keys(self) -> List[str]:
        if self.config.get("key_select_method", "from_list") == "from_list":
            return list(self.config.get("project_keys_list") or [])
        return list(self.config.get("project_keys_input") or [])

    def targets(self) -> List[Target]:
        existing = existing_project_keys(self.client)
        sandbox = self.client.get_project_folder(self.settings.sandbox_folder)
        user_folders = {f.get_name(): f for f in sandbox.list_child_folders()}
        project_keys = self.project_keys()

        targets = []
        for user_num in iter_user_nums(int(self.config["user_count"])):
            user = user_id(user_num)
            deps = []
            for project_key in project_keys:
                target_key = suffixed_key(project_key, user_num)
                if target_key in existing:
                    targets.append(Target(PROJECT, target_key, group=user))
                    deps.append(target_key)
                else:
                    print("Skip {} (does not exist)".format(target_key))

            folder = user_folders.get(user)
            if folder is None:
                print("Skip deleting folder {} (does not exist)".format(user))
            else:
                targets.append(Target(FOLDER, user, group=user, depends_on=tuple(deps), handle=folder))
        return targets


class AllUserFolders(DeletePlan):
    """``delete_type == "all_user_folders"``."""

    def targets(self) -> List[Target]:
        keep_keys = self.keep_keys()
        targets = []
        for user_folder in list_user_folders(self.client, self.settings.sandbox_folder):
            name = user_folder.get_name()
            self._plan_folder(user_folder, name, name, 0, keep_keys, targets)
        return targets

    def _plan_folder(self, folder, path: str, group: str, depth: int, keep_keys: Set[str], targets: List[Target]) -> bool:
        """Append the subtree's targets (children first); return True if the folder itself gets deleted."""
        deps = []
        all_children_deleted = True
        for child in folder.list_child_folders():
            child_path = "{}/{}".format(path, child.get_name())
            if self._plan_folder(child, child_path, group, depth + 1, keep_keys, targets):
                deps.append(child_path)
            else:
                all_children_deleted = False

        folder_clean = True
        for project_key in folder.list_project_keys():
            kept = project_key in keep_keys
            targets.append(Target(PROJECT, project_key, group=group, depth=depth, keep=kept))
            if kept:
                folder_clean = False
            else:
                deps.append(project_key)

        delete_folder = folder_clean and all_children_deleted
        targets.append(Target(FOLDER, path, group=group, depth=depth, keep=not delete_folder,
                              depends_on=tuple(deps), handle=folder))
        return delete_folder


class WholeFolder(DeletePlan):
    """``delete_type == "sandbox"`` or ``"root_folder"``: projects directly in that folder."""

    def folder(self):
        if self.config.get("delete_type") == "root_folder":
            return self.client.get_root_project_folder()
        return self.client.get_project_folder(self.settings.sandbox_folder)

    def targets(self) -> List[Target]:
        keep_keys = self.keep_keys()
        return [Target(PROJECT, key, keep=key in keep_keys) for key in self.folder().list_project_keys()]


PLANS = {
    "user_num": ByUserNum,
    "all_user_folders": AllUserFolders,
    "sandbox": WholeFolder,
    "root_folder": WholeFolder,
}


def build_plan(client, settings, config: Dict[str, Any], running_project_key: str) -> DeletePlan:
    """The :class:`DeletePlan` matching ``config["delete_type"]``."""
    delete_type = (config or {}).get("delete_type")
    if delete_type not in PLANS:
        raise ValueError("Unknown delete_type: {!r} (expected one of {})".format(delete_type, sorted(PLANS)))
    return PLANS[delete_type](client, settings, config, running_project_key)


def apply(targets: Iterable[Target], client, dry_run: bool,
          progress_callback: Optional[Callable[[int], None]] = None) -> DeleteResult:
    """Delete the targets in order (or only report them when ``dry_run``).

    A folder is skipped, and reported as a failure, when any item it depends on
    could not be deleted; that folder then blocks its own parent in turn.
    """
    result = DeleteResult(dry_run=dry_run)
    failed = set()

    for position, target in enumerate(targets, start=1):
        if progress_callback is not None:
            progress_callback(position)
        indent = "  " * target.depth

        if target.keep:
            print("{}Keep {} {}".format(indent, target.kind, target.key))
            result.kept.append(target)
            continue

        blockers = [key for key in target.depends_on if key in failed]
        if blockers:
            reason = "not deleted: {} could not be deleted".format(", ".join(blockers))
            print("{}Skip {} {} ({})".format(indent, target.kind, target.key, reason))
            result.failures.append((target.key, reason))
            failed.add(target.key)
            continue

        if dry_run:
            print("{}Would delete {} {}".format(indent, target.kind, target.key))
            result.done.append(target)
            continue

        try:
            if target.kind == PROJECT:
                delete_project(client, target.key)
            else:
                print("{}Delete folder {}".format(indent, target.key))
                target.handle.delete()
        except Exception as e:
            print("{}{} {} delete failed: {}".format(indent, target.kind, target.key, e))
            traceback.print_exc()
            result.failures.append((target.key, str(e)))
            failed.add(target.key)
            continue

        result.done.append(target)

    return result
