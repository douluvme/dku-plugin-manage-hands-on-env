# This file is the actual code for the Python runnable 3-2-get-db-class
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.aws import boto_client, RDS_INSTANCE_ID


class MyRunnable(HandsOnRunnable):
    """Report the current instance class and status of the workshop RDS database."""

    def execute(self, progress_callback):
        rds_client = boto_client('rds', self.config.get("aws_account"))

        response = rds_client.describe_db_instances(DBInstanceIdentifier=RDS_INSTANCE_ID)
        db_class = response['DBInstances'][0]['DBInstanceClass']
        db_status = response['DBInstances'][0]['DBInstanceStatus']

        return f"<p style='font-size:16px;'>Current DB class = <b>{db_class}</b></br>DB status = <b>{db_status}</b></p>"
