# This file is the actual code for the Python runnable manage-starter-project
from dataiku.runnables import Runnable
import dataiku
#from managehandsonenv.common_functions import *
import time

class MyRunnable(Runnable):
    def __init__(self, project_key, config, plugin_config):
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
    def get_progress_target(self):
        return (1, 'NONE')

    def run(self, progress_callback):
        config = self.config
        client = dataiku.api_client()

        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(10)
            return None

        project = client.get_project("READONLY")

        settings = project.get_settings()
        objects = settings.get_raw()['exposedObjects']['objects']
        rules = next((obj for obj in objects if obj['localName'] == 'credit_score'), None)['rules']

        index_list = []

        for x in range(0,len(rules)):
            if rules[x]['targetProject'].startswith('KO4EVAL') or rules[x]['targetProject'] == 'DEMO_KO_CARDFRAUD':
                pass
            else:
                print(f"Target project : {rules[x]['targetProject']}")
                index_list.append(x)

        for index in sorted(index_list, reverse=True):
            del rules[index]

        settings.save()

        print(f"Stopped sharing {len(index_list)} shared project(s)")

        progress_callback(1)

        return f"Stopped sharing {len(index_list)} shared project(s)"
