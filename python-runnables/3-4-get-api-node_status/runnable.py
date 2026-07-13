# This file is the actual code for the Python runnable manage-starter-project
from dataiku.runnables import Runnable
import dataiku
from managehandsonenv.common_functions import *
import time
import boto3

class MyRunnable(Runnable):
    def __init__(self, project_key, config, plugin_config):
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
    def get_progress_target(self):
        return None

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

        rds_client = boto3.client('rds',
            'ap-northeast-2',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)

        instance_id = 'i-0e7ccb12c93ac1df2'

        instance_name, instance_state = get_aws_ec2_instance_details(ec2_client, instance_id)

        return f"<p style='font-size:16px;'>Instance {instance_name} ({instance_id}) is <b>{instance_state.upper()}</b></p>"