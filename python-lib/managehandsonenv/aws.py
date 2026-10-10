"""boto3 helpers for the workshop infrastructure macros."""
import boto3


def boto_client(service, preset, region):
    """Build a boto3 client for ``service`` from an ``aws-credentials`` preset dict."""
    preset = preset or {}
    return boto3.client(
        service,
        region_name=region,
        aws_access_key_id=preset.get("aws_access_key_id"),
        aws_secret_access_key=preset.get("aws_secret_access_key"),
    )


def ec2_instance_details(ec2, instance_id):
    """Return ``(name_tag, state)`` for an EC2 instance, or ``(None, None)`` on error."""
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
