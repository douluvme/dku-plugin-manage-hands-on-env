"""Hands-on 1: prepare the starter projects for the attendees."""
import traceback
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from managehandsonenv.context import Context
from managehandsonenv.features.types import Feature
from managehandsonenv.projects import duplicate_project, existing_project_keys, set_project_owner, suffixed_key
from managehandsonenv.results import failures_section, grouped_lines, html_key, key_lines, render_result
from managehandsonenv.users import get_user_folder, iter_user_nums, iter_user_nums_range, user_id

CATEGORY = "⚠️ Hands-on 1: Manage Starter Projects"


def _selected_project_keys(params: Dict[str, Any]) -> List[str]:
    if params.get("key_select_method", "from_list") == "from_list":
        return list(params.get("project_keys_list") or [])
    return list(params.get("project_keys_input") or [])


# --- 1-1 duplicate ------------------------------------------------------------

def duplicate_starters_target(ctx: Context, params: Dict[str, Any]) -> Optional[int]:
    return len(_selected_project_keys(params)) * (int(params["user_count"]) + 1)


def duplicate_starters(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Duplicate the selected starter projects once per workshop user (instructor user99 first)."""
    client = ctx.client
    user_count = int(params["user_count"])
    project_keys = _selected_project_keys(params)
    total_progress_target = len(project_keys) * (user_count + 1)
    ctx.log("Progress target = {}".format(total_progress_target))
    ctx.log("Number of users = {}".format(user_count + 1))

    existing = existing_project_keys(client)
    created = OrderedDict()
    skipped = []
    failures = []
    total_dup_count = 0
    progress = 1

    for user_num in iter_user_nums(user_count):
        user = user_id(user_num)
        created[user] = []

        try:
            user_folder = get_user_folder(client, user, create=True, sandbox_folder=ctx.settings.sandbox_folder)
        except Exception as e:
            ctx.log("Failed to get/create folder for {}: {}".format(user, e))
            traceback.print_exc()
            failures.append((user, "folder: {}".format(e)))
            progress += len(project_keys)
            progress_callback(min(progress, total_progress_target))
            continue

        for project in project_keys:
            progress_callback(progress)
            progress += 1

            target_key = suffixed_key(project, user_num)
            if target_key in existing:
                ctx.log("Skip {} (already exists)".format(target_key))
                skipped.append(target_key)
                continue

            try:
                duplicate_project(client, project, target_key, user_folder)
            except Exception as e:
                ctx.log("{} duplication failed: {}".format(target_key, e))
                traceback.print_exc()
                failures.append((target_key, str(e)))
                continue

            existing.add(target_key)
            total_dup_count += 1
            created[user].append(html_key(target_key))

    return render_result(
        "Successfully duplicated {} project(s)".format(total_dup_count),
        grouped_lines(created),
        skipped=skipped,
        failures=failures,
    )


# --- 1-2 change owner ---------------------------------------------------------

def change_owner(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Change the owner of one starter project's copies (KEY_99, KEY_NN ...) to each user, or back to admin."""
    user_num_from = int(params["user_num_from"])
    user_num_to = int(params["user_num_to"])
    admin_TF = bool(params.get("admin_TF", False))

    project_key = (params["project_key_select"]
                   if params.get("key_select_method", "from_list") == "from_list"
                   else params["project_key_input"])

    total_update_count = 0
    # the instructor (user99) is always included
    for user_num in iter_user_nums_range(user_num_from, user_num_to):
        owner = "admin" if admin_TF else user_id(user_num)
        if set_project_owner(ctx.client, suffixed_key(project_key, user_num), owner):
            total_update_count += 1

    return "Successfully changed ownership for {} project(s)".format(total_update_count)


# --- 1-3 sandbox projects -> admin -------------------------------------------

def sandbox_to_admin(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Change the owner of every project directly in the sandbox folder to admin."""
    sandbox_folder = ctx.client.get_project_folder(ctx.settings.sandbox_folder)

    updated = []
    failures = []
    for project_key in sandbox_folder.list_project_keys():
        ctx.log("Project to update : {}".format(project_key))
        if set_project_owner(ctx.client, project_key, "admin"):
            updated.append(project_key)
        else:
            failures.append((project_key, "update failed"))

    progress_callback(1)

    return "Successfully changed owner of {} project(s) to admin</br></br>{}{}".format(
        len(updated), key_lines(updated), failures_section(failures)
    )


FEATURES = [
    Feature(
        id="duplicate_starters",
        label="1.Duplicate Starter Projects",
        category=CATEGORY,
        macro_folder="1-1-duplicate-starter-projects",
        run=duplicate_starters,
        progress_target=duplicate_starters_target,
        description="Duplicate starter projects for MLOps/LLM hands-on",
    ),
    Feature(
        id="change_owner",
        label="2.Change Projects Ownership",
        category=CATEGORY,
        macro_folder="1-2-change-owner-starter-projects",
        run=change_owner,
        description="Change owner of a selected starter project for specified number of users",
    ),
    Feature(
        id="sandbox_to_admin",
        label="3.Sandbox Projects → Admin",
        category=CATEGORY,
        macro_folder="1-3-change-owner-root-projects-to-admin",
        run=sandbox_to_admin,
        progress_target=lambda ctx, params: 1,
        description="Change owner of sandbox projects to admin",
    ),
]
