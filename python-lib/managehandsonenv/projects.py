"""Project-level operations: duplicate, change owner, delete, existence check."""
import traceback
from typing import Iterable, Optional, Set


def suffixed_key(project_key: str, user_num: str) -> str:
    """``("KO1COBUILD", "01")`` -> ``"KO1COBUILD_01"``."""
    return "{}_{}".format(project_key, user_num)


def existing_project_keys(client) -> Set[str]:
    """All project keys on the instance, as a set (one listing call)."""
    return set(client.list_project_keys())


def project_exists(client, project_key: str) -> bool:
    """True if ``project_key`` exists. Single listing call, no permission probing."""
    return project_key in existing_project_keys(client)


def duplicate_project(client, src_key: str, new_key: str, dest_folder, tags: Optional[Iterable[str]] = None) -> str:
    """Full duplication of ``src_key`` into ``dest_folder`` as ``new_key``; returns ``new_key``.

    The copy is tagged with ``tags``, by default ``["duplicated", <source label>]``.
    Raises on API error.
    """
    project = client.get_project(src_key)
    project_name = project.get_metadata()["label"]

    print("Start duplicating {}".format(new_key))
    project.duplicate(
        new_key,
        project_name,
        duplication_mode="FULL",
        target_project_folder=dest_folder,
        export_saved_models=True,
    )

    new_project = client.get_project(new_key)
    metadata = new_project.get_metadata()
    metadata["tags"] = list(tags) if tags is not None else ["duplicated", project_name]
    new_project.set_metadata(metadata)
    return new_key


def set_project_owner(client, project_key: str, owner: str) -> bool:
    """Set the owner of ``project_key``; returns False (and logs) on API error."""
    print("Set owner of {} to {}".format(project_key, owner))
    try:
        project = client.get_project(project_key)
        permissions = project.get_permissions()
        permissions["owner"] = owner
        project.set_permissions(permissions)
    except Exception as e:
        print("Failed to set owner of {}: {}".format(project_key, e))
        traceback.print_exc()
        return False
    return True


def delete_project(client, project_key: str) -> None:
    """Delete ``project_key`` with its managed datasets and job/scenario logs. Raises on API error."""
    print("Delete {}".format(project_key))
    client.get_project(project_key).delete(clear_managed_datasets=True, clear_job_and_scenario_logs=True)
