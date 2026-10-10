# This file is the actual code for the Python runnable 3-3-start-stop-api-node
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.common_functions import *
import boto3


class MyRunnable(HandsOnRunnable):
    """Start or stop the EC2 instance hosting the workshop API node."""

    def execute(self, progress_callback):
        config = self.config
        preset = config.get("aws_account", {})
        aws_access_key_id = preset.get("aws_access_key_id")
        aws_secret_access_key = preset.get("aws_secret_access_key")

        task = config["start_or_stop"]

        ec2_waiter = 'instance_running'
        if task == 'stop':
            ec2_waiter = 'instance_stopped'

        ec2_client = boto3.client('ec2',
            'ap-northeast-2',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

        instance_id = 'i-0e7ccb12c93ac1df2'
        instance_name, instance_state = get_aws_ec2_instance_details(ec2_client, instance_id)

        if task == 'start':
            if instance_state == 'running':
                result = f"Instance {instance_name} ({instance_id}) is already running"
            else:
                ec2_client.start_instances(InstanceIds=[instance_id])
                waiter = ec2_client.get_waiter(ec2_waiter)
                waiter.wait(InstanceIds=[instance_id])
                instance_name, instance_state = get_aws_ec2_instance_details(ec2_client, instance_id)
                result = f"Instance {instance_name} ({instance_id}) started</br>\
                    Current state = {instance_state}"
        else:
            if instance_state == 'stopped':
                result = f"Instance {instance_name} ({instance_id}) is already stopped"
            else:
                ec2_client.stop_instances(InstanceIds=[instance_id])
                waiter = ec2_client.get_waiter(ec2_waiter)
                waiter.wait(InstanceIds=[instance_id])
                instance_name, instance_state = get_aws_ec2_instance_details(ec2_client, instance_id)
                result = f"Instance {instance_name} ({instance_id}) stopped</br>\
                    Current state = {instance_state}"

        return result
