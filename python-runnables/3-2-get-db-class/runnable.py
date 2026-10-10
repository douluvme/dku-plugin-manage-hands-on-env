# Report the current RDS DB instance class and status of the workshop database.
from managehandsonenv.aws import boto_client
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    def execute(self, progress_callback):
        rds_client = boto_client('rds', self.aws_preset(), self.settings.aws_region)

        response = rds_client.describe_db_instances(DBInstanceIdentifier=self.settings.rds_instance_id)
        db_class = response['DBInstances'][0]['DBInstanceClass']
        db_status = response['DBInstances'][0]['DBInstanceStatus']

        return "<p style='font-size:16px;'>Current DB class = <b>{}</b></br>DB status = <b>{}</b></p>".format(db_class, db_status)
