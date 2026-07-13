# This file is the actual code for the Python runnable manage-starter-project
from dataiku.runnables import Runnable
import dataiku
#from managehandsonenv.common_functions import *
import time
import boto3

class MyRunnable(Runnable):
    def __init__(self, project_key, config, plugin_config):
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
    def get_progress_target(self):
        return (1, 'NONE')

    def run(self, progress_callback):
        preset = self.config.get("aws_account", {})
        aws_access_key_id = preset.get("aws_access_key_id")
        aws_secret_access_key = preset.get("aws_secret_access_key")
        # use as before, e.g. building a boto3 client
        config = self.config
        client = dataiku.api_client()

        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(10)
            return None

        db_class = config["db_class"]
        wait_TF = config["wait_TF"]

        rds_client = boto3.client('rds',
            'ap-northeast-2',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        
        response = rds_client.modify_db_instance(
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
