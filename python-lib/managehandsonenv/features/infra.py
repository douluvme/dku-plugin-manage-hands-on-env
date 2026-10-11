"""Hands-on 3: the AWS resources behind the workshop (RDS database, API-node EC2 instance)."""
import time
from typing import Any, Dict

from managehandsonenv.aws import boto_client, ec2_instance_details
from managehandsonenv.context import Context
from managehandsonenv.features.types import Feature

CATEGORY = "⚠️ Hands-on 3: Manage Workshop Environment"
MENU_CATEGORY = "Workshop Environment"


def _client(ctx: Context, params: Dict[str, Any], service: str):
    """A boto3 client for ``service``, after logging where the credentials come from."""
    ctx.log("AWS credentials: {}".format(ctx.aws_preset_source(params) or "not configured"))
    return boto_client(service, ctx.aws_preset(params), ctx.settings.aws_region)


# --- 3-1 modify DB class ------------------------------------------------------

def modify_db_class(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Modify the RDS DB instance class of the workshop database."""
    db_class = params["db_class"]
    wait_TF = params.get("wait_TF", False)
    db_instance_id = ctx.settings.rds_instance_id

    rds_client = _client(ctx, params, 'rds')
    rds_client.modify_db_instance(
        DBInstanceIdentifier=db_instance_id,
        DBInstanceClass=db_class,
        ApplyImmediately=True
    )

    return_message = "Started modifying DB class to <b>{}</b>. You'll have wait until the database is up and running.".format(db_class)

    if wait_TF:
        time.sleep(10)
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=db_instance_id)
        return_message = "Finished modifying DB class to <b>{}</b>".format(db_class)

    progress_callback(1)

    return "<p style='font-size:14px;'>{}</p>".format(return_message)


# --- 3-2 DB class & status ----------------------------------------------------

def db_status(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Report the current RDS DB instance class and status of the workshop database."""
    rds_client = _client(ctx, params, 'rds')

    response = rds_client.describe_db_instances(DBInstanceIdentifier=ctx.settings.rds_instance_id)
    db_class = response['DBInstances'][0]['DBInstanceClass']
    db_state = response['DBInstances'][0]['DBInstanceStatus']

    return "<p style='font-size:16px;'>Current DB class = <b>{}</b></br>DB status = <b>{}</b></p>".format(db_class, db_state)


# --- 3-3 start / stop API node ------------------------------------------------

def api_node_power(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Start or stop the EC2 instance hosting the API node."""
    task = params["start_or_stop"]
    instance_id = ctx.settings.api_node_instance_id

    ec2_client = _client(ctx, params, 'ec2')
    instance_name, instance_state = ec2_instance_details(ec2_client, instance_id, log=ctx.log)

    if task == 'start':
        if instance_state == 'running':
            return "Instance {} ({}) is already running".format(instance_name, instance_id)
        ec2_client.start_instances(InstanceIds=[instance_id])
        ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])
        instance_name, instance_state = ec2_instance_details(ec2_client, instance_id, log=ctx.log)
        return "Instance {} ({}) started</br>Current state = {}".format(instance_name, instance_id, instance_state)

    if instance_state == 'stopped':
        return "Instance {} ({}) is already stopped".format(instance_name, instance_id)
    ec2_client.stop_instances(InstanceIds=[instance_id])
    ec2_client.get_waiter('instance_stopped').wait(InstanceIds=[instance_id])
    instance_name, instance_state = ec2_instance_details(ec2_client, instance_id, log=ctx.log)
    return "Instance {} ({}) stopped</br>Current state = {}".format(instance_name, instance_id, instance_state)


# --- 3-4 API node status ------------------------------------------------------

def api_node_status(ctx: Context, params: Dict[str, Any], progress_callback) -> str:
    """Report whether the EC2 instance hosting the API node is running or stopped."""
    instance_id = ctx.settings.api_node_instance_id

    ec2_client = _client(ctx, params, 'ec2')
    instance_name, instance_state = ec2_instance_details(ec2_client, instance_id, log=ctx.log)

    if instance_state is None:
        return "<p style='font-size:16px;'>Instance {} could not be described (see the log)</p>".format(instance_id)

    return "<p style='font-size:16px;'>Instance {} ({}) is <b>{}</b></p>".format(
        instance_name, instance_id, instance_state.upper()
    )


FEATURES = [
    Feature(
        id="modify_db_class",
        settings_used=("aws_region", "rds_instance_id"),
        menu_label="Modify DB Size",
        menu_category=MENU_CATEGORY,
        label="1.Modify RDS DB size",
        category=CATEGORY,
        macro_folder="3-1-modify-db-class",
        run=modify_db_class,
        progress_target=lambda ctx, params: 1,
        destructive=True,
        confirm="The RDS instance class will be changed immediately; the database restarts and is unavailable meanwhile.",
        description="Modify RDS DB instance class according to the number of attendees",
    ),
    Feature(
        id="db_status",
        settings_used=("aws_region", "rds_instance_id"),
        menu_label="DB Status",
        menu_category=MENU_CATEGORY,
        label="2.Get RDS DB class & status",
        category=CATEGORY,
        macro_folder="3-2-get-db-class",
        run=db_status,
        description="Get current RDS DB instance class and status",
    ),
    Feature(
        id="api_node_power",
        settings_used=("aws_region", "api_node_instance_id"),
        menu_label="Start/Stop API Node",
        menu_category=MENU_CATEGORY,
        label="3.Start/Stop API node",
        category=CATEGORY,
        macro_folder="3-3-start-stop-api-node",
        run=api_node_power,
        destructive=True,
        confirm="The API node EC2 instance will be started or stopped.",
        description="Start or stop the API node for workshop environment",
    ),
    Feature(
        id="api_node_status",
        settings_used=("aws_region", "api_node_instance_id"),
        menu_label="API Node Status",
        menu_category=MENU_CATEGORY,
        label="4.Get API Node Status",
        category=CATEGORY,
        macro_folder="3-4-get-api-node_status",
        run=api_node_status,
        description="Check if API node is running or stopped",
    ),
]
