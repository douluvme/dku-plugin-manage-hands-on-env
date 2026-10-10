# This file is the actual code for the Python runnable manage-starter-project
import time

from managehandsonenv.aws import boto_client
from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    """Change the RDS instance class, optionally waiting until the database is available again."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        config = self.config
        db_class = config["db_class"]
        wait_TF = config["wait_TF"]
        rds_instance_id = self.settings.rds_instance_id

        rds_client = boto_client('rds', self.aws_preset(), self.settings.aws_region)

        rds_client.modify_db_instance(
            DBInstanceIdentifier=rds_instance_id,
            DBInstanceClass=db_class,
            ApplyImmediately=True
        )

        return_message = f"Started modifying DB class to <b>{db_class}</b>. You'll have wait until the database is up and running."

        if wait_TF:
            time.sleep(10)

            waiter = rds_client.get_waiter('db_instance_available')
            waiter.wait(DBInstanceIdentifier=rds_instance_id)

            return_message = f"Finished modifying DB class to <b>{db_class}</b>"

        progress_callback(1)

        return f"<p style='font-size:14px;'>{return_message}</p>"
