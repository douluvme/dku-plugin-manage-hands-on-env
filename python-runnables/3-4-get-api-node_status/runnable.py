# This file is the actual code for the Python runnable 3-4-get-api-node_status
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.aws import boto_client, ec2_instance_details, API_NODE_INSTANCE_ID


class MyRunnable(HandsOnRunnable):
    """Report whether the EC2 instance hosting the workshop API node is running."""

    def execute(self, progress_callback):
        ec2_client = boto_client('ec2', self.config.get("aws_account"))

        instance_id = API_NODE_INSTANCE_ID
        instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)

        if instance_state is None:
            raise RuntimeError(f"Could not read the state of instance {instance_id}; see the log for the AWS error")

        return f"<p style='font-size:16px;'>Instance {instance_name} ({instance_id}) is <b>{instance_state.upper()}</b></p>"
