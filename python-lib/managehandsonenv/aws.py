"""AWS helpers for the workshop infrastructure (RDS database and API-node EC2 instance).

Only the ``3-*`` macros import this module, so ``boto3`` is required only for them.
"""
import boto3

DEFAULT_REGION = "ap-northeast-2"
RDS_INSTANCE_ID = "postgres-mag"
API_NODE_INSTANCE_ID = "i-0e7ccb12c93ac1df2"


def boto_client(service, preset, region=DEFAULT_REGION):
    """Build a boto3 client for ``service`` from the ``aws-credentials`` preset dict
    (``aws_access_key_id`` / ``aws_secret_access_key``)."""
    preset = preset or {}
    return boto3.client(
        service,
        region,
        aws_access_key_id=preset.get("aws_access_key_id"),
        aws_secret_access_key=preset.get("aws_secret_access_key"),
    )


def ec2_instance_details(ec2, instance_id):
    """Return ``(name, state)`` of an EC2 instance, or ``(None, None)`` if it cannot be read."""
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])

        if not response.get('Reservations'):
            return None, None

        instance = response['Reservations'][0]['Instances'][0]
        tags = instance.get('Tags', [])

        name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), None)
        instance_state = instance['State']['Name']

        return name, instance_state

    except Exception as e:
        print(f"Error getting instance details: {str(e)}")
        return None, None
