"""Project-level helpers: existence, duplication, ownership and deletion."""
import traceback


def suffixed_key(project_key, num):
    """Per-user project key: ``("KO1COBUILD", "07") -> "KO1COBUILD_07"``."""
    return f"{project_key}_{num}"


def project_exists(client, project_key):
    """True if ``project_key`` exists. Single listing call, no permission probing."""
    return project_key in set(client.list_project_keys())


def duplicate_project(client, src_key, new_key, dest_folder, tags=None):
    """Full-duplicate ``src_key`` as ``new_key`` into ``dest_folder`` and tag it.

    Tags default to ``['duplicated', <source project label>]``.
    Raises whatever the DSS API raises; callers decide how to report it.
    Returns ``new_key``.
    """
    project = client.get_project(src_key)
    project_name = project.get_metadata()['label']

    print(f"Start duplicating {new_key}")
    project.duplicate(
        new_key,
        project_name,
        duplication_mode='FULL',
        target_project_folder=dest_folder,
        export_saved_models=True,
    )

    new_project = client.get_project(new_key)
    metadata = new_project.get_metadata()
    metadata['tags'] = list(tags) if tags is not None else ['duplicated', project_name]
    new_project.set_metadata(metadata)

    return new_key


def set_project_owner(client, project_key, owner):
    """Set the owner of ``project_key``. Returns False (and logs) on API error."""
    print(f"Set owner of {project_key} to {owner}")
    try:
        project = client.get_project(project_key)
        permissions = project.get_permissions()
        permissions['owner'] = owner
        project.set_permissions(permissions)
    except Exception as e:
        print(f"Failed to set owner of {project_key}: {e}")
        traceback.print_exc()
        return False
    return True


def delete_project(client, project_key):
    """Delete ``project_key`` with its managed datasets and logs. Returns False (and logs) on error."""
    print(f"Delete {project_key}")
    try:
        client.get_project(project_key).delete(
            clear_managed_datasets=True,
            clear_job_and_scenario_logs=True,
        )
    except Exception as e:
        print(f"Failed to delete {project_key}: {e}")
        traceback.print_exc()
        return False
    return True
