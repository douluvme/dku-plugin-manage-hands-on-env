# This file is the actual code for the Python runnable manage-starter-project
import boto3

from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    """Report the current RDS instance class and status."""

    def execute(self, progress_callback):
        preset = self.config.get("aws_account", {})
        aws_access_key_id = preset.get("aws_access_key_id")
        aws_secret_access_key = preset.get("aws_secret_access_key")

        rds_client = boto3.client('rds',
            'ap-northeast-2',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

        response = rds_client.describe_db_instances(DBInstanceIdentifier='postgres-mag')
        db_class = response['DBInstances'][0]['DBInstanceClass']
        db_status = response['DBInstances'][0]['DBInstanceStatus']

        return f"<p style='font-size:16px;'>Current DB class = <b>{db_class}</b></br>DB status = <b>{db_status}</b></p>"
