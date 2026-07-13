# This file is the actual code for the Python runnable manage-starter-project
from dataiku.runnables import Runnable
import dataiku
from managehandsonenv.common_functions import *
import time


class MyRunnable(Runnable):
    def __init__(self, project_key, config, plugin_config):
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        self.total_progress_target = len(config["project_key_list"]) * config["user_count"]

    def get_progress_target(self):
        return (self.total_progress_target, 'NONE')

    def run(self, progress_callback):
        config = self.config
        client = dataiku.api_client()
        number_of_users = int(config["user_count"])

        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(5)
            return None
        
#        print(f"config = {config}")

        print(f"Number of users = {number_of_users}")
        
        result_string = ""
        total_delete_count = 0
        
        progress = 1
        for x in range(number_of_users):
            if x == 0:
                user_num = '99'
                result_string = f"user99 :"
            else:
                user_num = str(x).zfill(2)
                result_string = f"{result_string}</br>user{user_num} :"

            user_folder = get_user_folder_by_id(client, 'user' + user_num, create_if_not_exist_TF=False)

            for project in config["project_key_list"]:    
                progress_callback(progress)
                result = delete_project_by_num(client, project, user_num)
                total_delete_count += result
                if result == 1:
                    result_string = f"{result_string} &lt;{project}&gt;"
                progress += 1
            
            print(user_folder)
            
            if user_folder == "":
                print("Skip")
            else:
                try:
                    user_folder.delete()
                except:
                    print('failed deleting folder')

        return f"Successfully deleted {total_delete_count} project(s)</br></br>{result_string}"
        