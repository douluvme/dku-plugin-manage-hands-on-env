# Report whether the EC2 instance hosting the API node is running or stopped.
from managehandsonenv.aws import boto_client, ec2_instance_details
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    def execute(self, progress_callback):
        instance_id = self.settings.api_node_instance_id

        ec2_client = boto_client('ec2', self.aws_preset(), self.settings.aws_region)
        instance_name, instance_state = ec2_instance_details(ec2_client, instance_id)

        if instance_state is None:
            return "<p style='font-size:16px;'>Instance {} could not be described (see the macro log)</p>".format(instance_id)

        return "<p style='font-size:16px;'>Instance {} ({}) is <b>{}</b></p>".format(
            instance_name, instance_id, instance_state.upper()
        )
