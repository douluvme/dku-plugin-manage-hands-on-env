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
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def run(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        
        config = self.config
        client = dataiku.api_client()
#        number_of_users = int(config["user_count"])
        user_num_from = int(config["user_num_from"])
        user_num_to = int(config["user_num_to"])
        admin_TF = config["admin_TF"]

        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(5)
            return None
        
#        print(f"config = {config}")

        total_update_count = 0
        project_key = config["project_key_select"] if config["key_select_method"] == "from_list" else config["project_key_input"]
    
        # 99 for instructor
        total_update_count += set_project_owner_by_num(client, project_key, '99', set_owner_to_admin_TF=admin_TF)

        for x in range(user_num_from, user_num_to + 1):
            total_update_count += set_project_owner_by_num(client, project_key, str(x).zfill(2), set_owner_to_admin_TF=admin_TF)

#        for x in range(number_of_users):
#            if x == 0:
#                user_num = '99'
#            else:
#                user_num = str(x).zfill(2)
            
#            total_update_count += set_project_owner_by_num(client, config["project_key"], user_num, set_owner_to_admin_TF=admin_TF)

#            if config["admin_TF"] == False:
#                total_update_count += set_project_owner_by_num(client, config["project_key"], user_num)
#            else:
#                total_update_count += set_project_owner_by_num(client, config["project_key"], user_num, set_owner_to_admin_TF=True)

        return f"Successfully changed ownership for {total_update_count} project(s)"

            