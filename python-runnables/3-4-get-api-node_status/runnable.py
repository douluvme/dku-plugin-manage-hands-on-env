# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.aws import boto_client, ec2_instance_details
from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    """Report whether the API node EC2 instance is running or stopped."""

    def execute(self, progress_callback):
        instance_id = self.settings.api_node_instance_id

        ec2_client = boto_client('ec2', self.aws_preset(), self.settings.aws_region)

        instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)
        state_label = instance_state.upper() if instance_state else "UNKNOWN"

        return f"<p style='font-size:16px;'>Instance {instance_name} ({instance_id}) is <b>{state_label}</b></p>"
