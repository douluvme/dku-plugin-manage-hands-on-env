# This file is the actual code for the Python runnable manage-starter-project
import time

import boto3

from managehandsonenv.base import HandsOnRunnable


class MyRunnable(HandsOnRunnable):
    """Change the RDS instance class, optionally waiting until the database is available again."""

    def get_progress_target(self):
        return (1, 'NONE')

    def execute(self, progress_callback):
        preset = self.config.get("aws_account", {})
        aws_access_key_id = preset.get("aws_access_key_id")
        aws_secret_access_key = preset.get("aws_secret_access_key")
        config = self.config

        db_class = config["db_class"]
        wait_TF = config["wait_TF"]

        rds_client = boto3.client('rds',
            'ap-northeast-2',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

        rds_client.modify_db_instance(
            DBInstanceIdentifier='postgres-mag',
            DBInstanceClass=db_class,
            ApplyImmediately=True
        )

        return_message = f"Started modifying DB class to <b>{db_class}</b>. You'll have wait until the database is up and running."

        if wait_TF:
            time.sleep(10)

            waiter = rds_client.get_waiter('db_instance_available')
            waiter.wait(DBInstanceIdentifier='postgres-mag')

            return_message = f"Finished modifying DB class to <b>{db_class}</b>"

        progress_callback(1)

        return f"<p style='font-size:14px;'>{return_message}</p>"
