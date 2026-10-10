"""Hands-on 2: tear the workshop down again."""
import re
from collections import OrderedDict
from typing import Any, Dict, Optional

from managehandsonenv.context import Context
from managehandsonenv.deletion import PROJECT, apply, build_plan
from managehandsonenv.features.types import Feature
from managehandsonenv.results import failures_section, folder_marker, grouped_lines, heading, html_key, key_lines
from managehandsonenv.users import INSTRUCTOR_NUM, user_id

CATEGORY = "⚠️ Hands-on 2: Housekeeping"

ATTENDEE_LOGIN_PATTERN = re.compile(r"^user[0-9]{2}")
DEFAULT_TARGETS_TO_KEEP = ["KO4EVAL", "DEMO_KO_CARDFRAUD"]


# --- 2-1 delete ---------------------------------------------------------------

def _delete_targets(ctx: Context, params: Dict[str, Any]):
    plan = build_plan(ctx.client, ctx.settings, params, ctx.project_key, log=ctx.log)
    return plan.targets()


def delete_projects_target(ctx: Context, params: Dict[str, Any]) -> Optional[int]:
    targets = _delete_targets(ctx, params)
    ctx.log("Progress target = {}".format(len(targets)))
    return max(len(targets), 1)


def delete_projects(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Delete starter projects (by user number, per user folder, or a whole folder), with a dry-run mode."""
    targets = _delete_targets(ctx, params)
    dry_run = not params.get("delete_TF", False)
    result = apply(targets, ctx.client, dry_run=dry_run, progress_callback=progress_callback, log=ctx.log)

    if dry_run:
        title = "Identified {} project(s) to delete".format(len(result.projects))
        verb = "Identified"
    else:
        title = "Successfully deleted {} project(s)".format(len(result.projects))
        verb = "Deleted"

    if not any(t.group for t in targets):  # whole-folder modes: flat listing
        body = key_lines(t.key for t in result.projects)
    else:
        # one line per user folder, in plan order, even when nothing in it is deleted
        groups = OrderedDict((t.group, []) for t in targets)
        for target in result.done:
            groups[target.group].append(html_key(target.key) if target.kind == PROJECT else folder_marker(target.key))
        body = grouped_lines(groups)

    return (
        heading(title)
        + body
        + heading("{} {} user folder(s)".format(verb, len(result.folders)))
        + failures_section(result.failures)
    )


# --- 2-2 enable / disable attendees -------------------------------------------

def toggle_users(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Enable or disable every attendee user (userNN); the instructor (user99) is never touched."""
    enable_or_disable = params["enable_or_disable"]
    user_enabled = enable_or_disable != "disable"
    instructor = user_id(INSTRUCTOR_NUM)

    total_update_count = 0
    for dss_user in ctx.client.list_users():
        login = dss_user["login"]
        if ATTENDEE_LOGIN_PATTERN.search(login) is not None and login != instructor:
            ctx.log("{} {}".format(enable_or_disable, login))
            user_settings = ctx.client.get_user(login).get_settings()
            user_settings.enabled = user_enabled
            user_settings.save()
            total_update_count += 1
        else:
            ctx.log("Skip {}".format(login))

    return "Successfully {}d {} user(s)".format(enable_or_disable, total_update_count)


# --- 2-3 clean deployed APIs and bundles --------------------------------------

def clean_deployments_target(ctx: Context, params: Dict[str, Any]) -> Optional[int]:
    api_or_bundle = params["api_or_bundle"]
    total_progress_count = 0

    if api_or_bundle in ['api', 'both']:
        try:
            apideployer = ctx.client.get_apideployer()
            api_deployments = apideployer.list_deployments() or []
            api_services = apideployer.list_services() or []
            total_progress_count += len(api_deployments) + len(api_services)
        except Exception as e:
            ctx.log("Error getting API deployments/services: {}".format(e))

    if api_or_bundle in ['bundle', 'both']:
        try:
            projectdeployer = ctx.client.get_projectdeployer()
            project_deployments = projectdeployer.list_deployments() or []
            project_bundles = projectdeployer.list_projects() or []
            total_progress_count += len(project_deployments) + len(project_bundles)
        except Exception as e:
            ctx.log("Error getting project deployments/bundles: {}".format(e))

    return total_progress_count


def clean_deployments(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Remove deployed API deployments/services and project deployments/bundles, except protected ones."""
    api_or_bundle = params["api_or_bundle"]
    protected_prefix = ctx.settings.protected_bundle_prefix
    result_string = ""
    api_deployment_count = 0
    api_service_count = 0
    prj_deployment_count = 0
    prj_bundle_count = 0
    progress = 1

    if api_or_bundle in ['api', 'both']:
        apideployer = ctx.client.get_apideployer()
        deployments = apideployer.list_deployments()
        ctx.log("No of deployments = {}".format(len(deployments)))
        api_deployment_count = len(deployments)
        result_string = "</br>&lt;List of API deployment&gt;"

        for deployment in deployments:
            ctx.log("### Deployment ID = {}".format(deployment.id))
            settings = deployment.get_settings()
            settings.set_enabled(enabled=False)
            settings.save(ignore_warnings=False)
            futurestate = deployment.start_update()
            futurestate.wait_for_result()

            deployment.delete(disable_first=True, ignore_pre_delete_errors=False)
            result_string = "{}</br>- {}".format(result_string, deployment.id)
            progress_callback(progress)
            progress += 1

        services = apideployer.list_services()
        ctx.log("No of services = {}".format(len(services)))
        api_service_count = len(services)
        result_string = "{}</br></br>&lt;List of API service&gt;".format(result_string)

        for service in services:
            ctx.log("### Service ID = {}".format(service.id))
            service.delete()
            result_string = "{}</br>- {}".format(result_string, service.id)
            progress_callback(progress)
            progress += 1

    if api_or_bundle in ['bundle', 'both']:
        projectdeployer = ctx.client.get_projectdeployer()
        project_deployments = projectdeployer.list_deployments()
        ctx.log("No of project deployments = {}".format(len(project_deployments)))
        prj_deployment_count = len(project_deployments)
        result_string = "{}</br></br>&lt;List of project deployment&gt;".format(result_string)

        for deployment in project_deployments:
            if deployment.id.startswith(protected_prefix):
                ctx.log("Skip {}".format(deployment.id))
            else:
                ctx.log("### Project Deployment ID = {}".format(deployment.id))
                deployment.delete()
                result_string = "{}</br>- {}".format(result_string, deployment.id)

            progress_callback(progress)
            progress += 1

        bundles = projectdeployer.list_projects()
        ctx.log("No of bundles = {}".format(len(bundles)))
        prj_bundle_count = len(bundles)
        result_string = "{}</br></br>&lt;List of project bundle&gt;".format(result_string)

        for bundle in bundles:
            if bundle.id.startswith(protected_prefix):
                ctx.log("Skip {}".format(bundle.id))
            else:
                ctx.log("### Project Bundle ID = {}".format(bundle.id))
                bundle.delete()
                result_string = "{}</br>- {}".format(result_string, bundle.id)

            progress_callback(progress)
            progress += 1

    return "Successfully deleted {} API deployment(s) and {} service(s)</br> \
            {} project deployment(s) and {} bundle(s) \
            {}".format(api_deployment_count, api_service_count, prj_deployment_count, prj_bundle_count, result_string)


# --- 2-4 stop sharing ---------------------------------------------------------

def stop_sharing(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Stop sharing the shared dataset of the read-only project with every project not in the keep list."""
    readonly_key = ctx.settings.readonly_project_key
    dataset_name = ctx.settings.shared_dataset_name
    keep_prefixes = params.get("target_projects_to_keep")
    if keep_prefixes is None:  # parameter absent (older saved config): historical behaviour
        keep_prefixes = DEFAULT_TARGETS_TO_KEEP
    keep_prefixes = [p for p in keep_prefixes if p]

    project = ctx.client.get_project(readonly_key)
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
            ctx.log("Keep sharing with {}".format(target))
        else:
            ctx.log("Target project : {}".format(target))
            index_list.append(index)

    for index in sorted(index_list, reverse=True):
        del rules[index]

    settings.save()

    ctx.log("Stopped sharing {} shared project(s)".format(len(index_list)))
    progress_callback(1)

    return "Stopped sharing {} shared project(s)".format(len(index_list))


FEATURES = [
    Feature(
        id="delete_projects",
        label="1.Delete Starter Projects",
        category=CATEGORY,
        macro_folder="2-1-delete-starter-projects",
        run=delete_projects,
        progress_target=delete_projects_target,
        destructive=True,
        confirm="Projects (and emptied user folders) will be permanently deleted. Run a dry run first if unsure.",
        description="Delete starter projects for MLOps/LLM hands-on",
    ),
    Feature(
        id="toggle_users",
        label="2.Enable/disable Attendee Users",
        category=CATEGORY,
        macro_folder="2-2-enable-disable-attendee-users",
        run=toggle_users,
        destructive=True,
        confirm="Every userNN account (except the instructor user99) will be enabled or disabled.",
        description="Enable or disable Attendee Users",
    ),
    Feature(
        id="clean_deployments",
        label="3.Clean Deployed APIs and Bundles",
        category=CATEGORY,
        macro_folder="2-3-clean-deployed-apis-and-bundles",
        run=clean_deployments,
        progress_target=clean_deployments_target,
        destructive=True,
        confirm="All API deployments/services and unprotected project deployments/bundles will be deleted.",
        description="Remove deployed API deployments and services. Remove deployed project deployments and bundles",
    ),
    Feature(
        id="stop_sharing",
        label="4.Stop Sharing Datasets",
        category=CATEGORY,
        macro_folder="2-4-stop-sharing-datasets",
        run=stop_sharing,
        progress_target=lambda ctx, params: 1,
        destructive=True,
        confirm="Sharing rules of the read-only project's dataset will be removed for every project not in the keep list.",
        description="Stop sharing the read-only project's shared dataset (plugin settings) with starter projects",
    ),
]
