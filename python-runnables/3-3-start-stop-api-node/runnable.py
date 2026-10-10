# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.aws import boto_client, ec2_instance_details
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    """Start or stop the API node EC2 instance and wait for the target state."""

    def execute(self, progress_callback):
        config = self.config
        task = config["start_or_stop"]
        instance_id = self.settings.api_node_instance_id

        ec2_waiter = 'instance_running'
        if task == 'stop':
            ec2_waiter = 'instance_stopped'

        ec2_client = boto_client('ec2', self.aws_preset(), self.settings.aws_region)

        instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)

        if task == 'start':
            if instance_state == 'running':
                result = f"Instance {instance_name} ({instance_id}) is already running"
            else:
                ec2_client.start_instances(InstanceIds=[instance_id])
                waiter = ec2_client.get_waiter(ec2_waiter)
                waiter.wait(InstanceIds=[instance_id])
                instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)
                result = (f"Instance {instance_name} ({instance_id}) started</br>"
                          f"Current state = {instance_state}")
        else:
            if instance_state == 'stopped':
                result = f"Instance {instance_name} ({instance_id}) is already stopped"
            else:
                ec2_client.stop_instances(InstanceIds=[instance_id])
                waiter = ec2_client.get_waiter(ec2_waiter)
                waiter.wait(InstanceIds=[instance_id])
                instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)
                result = (f"Instance {instance_name} ({instance_id}) stopped</br>"
                          f"Current state = {instance_state}")

        return result
