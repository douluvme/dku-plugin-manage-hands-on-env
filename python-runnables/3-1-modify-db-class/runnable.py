# This file is the actual code for the Python runnable 3-1-modify-db-class
from managehandsonenv import base
from managehandsonenv.aws import boto_client, RDS_INSTANCE_ID
import time


class MyRunnable(base.HandsOnRunnable):
    """Change the instance class of the workshop RDS database."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        config = self.config
        db_class = config["db_class"]
        wait_TF = config["wait_TF"]

        rds_client = boto_client('rds', config.get("aws_account"))

        rds_client.modify_db_instance(
            DBInstanceIdentifier=RDS_INSTANCE_ID,
            DBInstanceClass=db_class,
            ApplyImmediately=True
        )

        return_message = f"Started modifying DB class to <b>{db_class}</b>. You'll have wait until the database is up and running."

        if wait_TF:
            time.sleep(10)

            waiter = rds_client.get_waiter('db_instance_available')
            waiter.wait(DBInstanceIdentifier=RDS_INSTANCE_ID)

            return_message = f"Finished modifying DB class to <b>{db_class}</b>"

        progress_callback(1)

        return f"<p style='font-size:14px;'>{return_message}</p>"
