"""boto3 helpers for the workshop infrastructure macros."""
from typing import Any, Dict, Optional, Tuple

import boto3


def boto_client(service: str, preset: Dict[str, Any], region: str):
    """A boto3 client for ``service`` authenticated with the ``aws-credentials`` preset."""
    return boto3.client(
        service,
        region_name=region,
        aws_access_key_id=preset.get("aws_access_key_id"),
        aws_secret_access_key=preset.get("aws_secret_access_key"),
    )


def ec2_instance_details(ec2, instance_id: str) -> Tuple[Optional[str], Optional[str]]:
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
        print("Error getting instance details: {}".format(e))
        return None, None
