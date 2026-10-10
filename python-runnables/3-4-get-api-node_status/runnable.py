# This file is the actual code for the Python runnable manage-starter-project
import boto3

from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.common_functions import get_aws_ec2_instance_details


class MyRunnable(HandsOnRunnable):
    """Report whether the API node EC2 instance is running or stopped."""

    def execute(self, progress_callback):
        preset = self.config.get("aws_account", {})
        aws_access_key_id = preset.get("aws_access_key_id")
        aws_secret_access_key = preset.get("aws_secret_access_key")

        ec2_client = boto3.client('ec2',
            'ap-northeast-2',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

        instance_id = 'i-0e7ccb12c93ac1df2'

        instance_name, instance_state = get_aws_ec2_instance_details(ec2_client, instance_id)
        state_label = instance_state.upper() if instance_state else "UNKNOWN"

        return f"<p style='font-size:16px;'>Instance {instance_name} ({instance_id}) is <b>{state_label}</b></p>"
