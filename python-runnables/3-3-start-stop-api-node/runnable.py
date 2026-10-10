# Start or stop the EC2 instance hosting the API node.
from managehandsonenv.aws import boto_client, ec2_instance_details
from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    def execute(self, progress_callback):
        task = self.config["start_or_stop"]
        instance_id = self.settings.api_node_instance_id

        ec2_client = boto_client('ec2', self.aws_preset(), self.settings.aws_region)
        instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)

        if task == 'start':
            if instance_state == 'running':
                return "Instance {} ({}) is already running".format(instance_name, instance_id)
            ec2_client.start_instances(InstanceIds=[instance_id])
            ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])
            instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)
            return "Instance {} ({}) started</br>Current state = {}".format(instance_name, instance_id, instance_state)

        if instance_state == 'stopped':
            return "Instance {} ({}) is already stopped".format(instance_name, instance_id)
        ec2_client.stop_instances(InstanceIds=[instance_id])
        ec2_client.get_waiter('instance_stopped').wait(InstanceIds=[instance_id])
        instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)
        return "Instance {} ({}) stopped</br>Current state = {}".format(instance_name, instance_id, instance_state)
