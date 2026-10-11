"""boto3 helpers for the workshop infrastructure features."""
from typing import Any, Dict, Optional, Tuple

NO_CREDENTIALS_MESSAGE = (
    "No AWS credentials: select an AWS Account in the webapp settings (Settings tab) "
    "or in the plugin settings; macros use their own AWS Account parameter"
)


def boto_client(service: str, preset: Dict[str, Any], region: str):
    """A boto3 client for ``service`` authenticated with the ``aws-credentials`` preset.

    Raises ``RuntimeError`` when the preset carries no key pair rather than letting
    boto3 fall back to the instance role, whose permissions are not the plugin's.

    ``boto3`` is imported here, not at module level, so that the library (and the
    macros that never touch AWS) can be imported where it is not installed.
    """
    preset = preset or {}
    if not (preset.get("aws_access_key_id") and preset.get("aws_secret_access_key")):
        raise RuntimeError(NO_CREDENTIALS_MESSAGE)
    try:
        import boto3
    except ImportError:
        raise RuntimeError(
            "boto3 is not installed: build the plugin code environment "
            "(Plugins > manage-hands-on-env > Settings > Code env)"
        )
    return boto3.client(
        service,
        region_name=region,
        aws_access_key_id=preset.get("aws_access_key_id"),
        aws_secret_access_key=preset.get("aws_secret_access_key"),
    )


def ec2_instance_details(ec2, instance_id: str, log=print) -> Tuple[Optional[str], Optional[str]]:
    """``(name, state)`` of an EC2 instance, or ``(None, None)`` if it cannot be described."""
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        if not response.get("Reservations"):
            return None, None

        instance = response["Reservations"][0]["Instances"][0]
        tags = instance.get("Tags", [])
        name = next((tag["Value"] for tag in tags if tag["Key"] == "Name"), None)
        return name, instance["State"]["Name"]
    except Exception as e:
        log("Error getting instance details: {}".format(e))
        return None, None
