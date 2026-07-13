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
        client = dataiku.api_client()
        self.client = client

    def get_progress_target(self):
        return (1, 'NONE')

    def run(self, progress_callback):
        config = self.config
        client = self.client
        total_update_count = 0
        result_string = ""
        
        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(5)
            return None

        #root_folder = client.get_root_project_folder()
        #project_list = root_folder.list_project_keys()
        sandbox_folder = client.get_project_folder('SANDBOX')
        project_list = sandbox_folder.list_project_keys()

        for project_id in project_list:

            try:
                print("Project to update :", project_id)
                print(f"Update {project_id}")                
                total_update_count += set_project_owner(client, project_id, 'admin')
                result_string = f"{result_string}&lt;{project_id}&gt;</br>"
            except:
                print(f"{project_id} update failed")


        progress_callback(1)
        
        return_msg = f"Successfully changed owner of {total_update_count} project(s) to admin</br></br>{result_string}" 
        return return_msg
        