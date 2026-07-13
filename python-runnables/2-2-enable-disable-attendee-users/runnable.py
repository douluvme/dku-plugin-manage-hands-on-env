# This file is the actual code for the Python runnable manage-starter-project
from dataiku.runnables import Runnable
import dataiku
from managehandsonenv.common_functions import *
import time


class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
    def get_progress_target(self):
        return None

    def run(self, progress_callback):
        import re
        
        config = self.config
        client = dataiku.api_client()
        enable_or_disable = config["enable_or_disable"]
        user_enabled = True

        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(10)
            return None

        if enable_or_disable == "disable":
            user_enabled = False

        dss_users = client.list_users()
        total_update_count = 0
        
        for dss_user in dss_users:
            user_id = dss_user["login"]
            if re.search("^user[0-9]{2}", user_id) != None and user_id != 'user99':
                print(f"{enable_or_disable} {user_id}")
                user = client.get_user(user_id)
                user_settings = user.get_settings()
                user_settings.enabled = user_enabled
                user_settings.save()
                total_update_count += 1
            else:
                print(f"Skip {user_id}")

        return f"Successfully {enable_or_disable}d {total_update_count} user(s)"
