# Modify the RDS DB instance class of the workshop database.
import time

from managehandsonenv.aws import boto_client
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        db_class = self.config["db_class"]
        wait_TF = self.config["wait_TF"]
        db_instance_id = self.settings.rds_instance_id

        rds_client = boto_client('rds', self.aws_preset(), self.settings.aws_region)
        rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_id,
            DBInstanceClass=db_class,
            ApplyImmediately=True
        )

        return_message = "Started modifying DB class to <b>{}</b>. You'll have wait until the database is up and running.".format(db_class)

        if wait_TF:
            time.sleep(10)
            waiter = rds_client.get_waiter('db_instance_available')
            waiter.wait(DBInstanceIdentifier=db_instance_id)
            return_message = "Finished modifying DB class to <b>{}</b>".format(db_class)

        progress_callback(1)

        return "<p style='font-size:14px;'>{}</p>".format(return_message)
