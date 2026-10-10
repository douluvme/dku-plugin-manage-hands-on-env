# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.aws import boto_client
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    """Report the current RDS instance class and status."""

    def execute(self, progress_callback):
        rds_client = boto_client('rds', self.aws_preset(), self.settings.aws_region)

        response = rds_client.describe_db_instances(DBInstanceIdentifier=self.settings.rds_instance_id)
        db_class = response['DBInstances'][0]['DBInstanceClass']
        db_status = response['DBInstances'][0]['DBInstanceStatus']

        return f"<p style='font-size:16px;'>Current DB class = <b>{db_class}</b></br>DB status = <b>{db_status}</b></p>"
