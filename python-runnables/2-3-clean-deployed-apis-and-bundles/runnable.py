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

        client = dataiku.api_client()
        apideployer = client.get_apideployer()
        projectdeployer = client.get_projectdeployer()
        self.client = client
        self.apideployer = apideployer
        self.projectdeployer = client.get_projectdeployer()

        api_or_bundle = config["api_or_bundle"]

        total_progress_count = 0

        if api_or_bundle in ['api', 'both']:
            try:
                api_deployments = apideployer.list_deployments() or []
                api_services = apideployer.list_services() or []
                total_progress_count += len(api_deployments) + len(api_services)
            except Exception as e:
                print(f"Error getting API deployments/services: {str(e)}")

        if api_or_bundle in ['bundle', 'both']:
            try:
                project_deployments = projectdeployer.list_deployments() or []
                project_bundles = projectdeployer.list_projects() or []
                total_progress_count += len(project_deployments) + len(project_bundles)
            except Exception as e:
                print(f"Error getting project deployments/bundles: {str(e)}")
            
        self.progress_target = total_progress_count

    def get_progress_target(self):
        return (self.progress_target, 'NONE')

    def run(self, progress_callback):
        config = self.config
        client = self.client
        apideployer = self.apideployer
        projectdeployer = self.projectdeployer
        api_or_bundle = config["api_or_bundle"]
        result_string = ""
        api_deployment_count = 0
        api_service_count = 0
        prj_deployment_count = 0
        prj_bundle_count = 0
        progress = 1
        
        if self.project_key != 'ADMINV4':
            print("This macro can be run only from admin project")
            time.sleep(10)
            return None

        if api_or_bundle in ['api', 'both']:
            deployments = apideployer.list_deployments()
            print("No of deployments = ", len(deployments))
            api_deployment_count = len(deployments)
            result_string = f"</br>&lt;List of API deployment&gt;"

            for deployment in deployments:
                print("### Deployment ID = ", deployment.id)
                settings = deployment.get_settings()
                settings.set_enabled(enabled=False)
                settings.save(ignore_warnings=False)
                futurestate = deployment.start_update()
                futurestate.wait_for_result()

                deployment.delete(disable_first=True, ignore_pre_delete_errors=False)
                result_string = f"{result_string}</br>- {deployment.id}"
                progress_callback(progress)
                progress += 1

            services = apideployer.list_services()
            print("No of services = ", len(services))
            api_service_count = len(services)
            result_string = f"{result_string}</br></br>&lt;List of API service&gt;"

            for service in services:
                settings = service.get_settings()
                print("### Service ID = ", service.id)
                service.delete()
                result_string = f"{result_string}</br>- {service.id}"
                progress_callback(progress)
                progress += 1

        if api_or_bundle in ['bundle', 'both']:
            project_deployments = projectdeployer.list_deployments()
            print("No of project deployments = ", len(project_deployments))
            prj_deployment_count = len(project_deployments)
            result_string = f"{result_string}</br></br>&lt;List of project deployment&gt;"

            for deployment in project_deployments:
                if deployment.id.startswith('READONLY'):
                    pass
                    print("Skip", deployment.id)
                else:
                    print("### Project Deployment ID = ", deployment.id)
                    deployment.delete()
                    result_string = f"{result_string}</br>- {deployment.id}"

                progress_callback(progress)
                progress += 1

            bundles = projectdeployer.list_projects()
            print("No of bundles = ", len(bundles))
            prj_bundle_count = len(bundles)
            result_string = f"{result_string}</br></br>&lt;List of project bundle&gt;"

            for bundle in bundles:
                if bundle.id.startswith('READONLY'):
                    pass
                    print("Skip", bundle.id)
                else:
                    print("### Project Bundle ID = ", bundle.id)
                    bundle.delete()
                    result_string = f"{result_string}</br>- {bundle.id}"

                progress_callback(progress)
                progress += 1
        
        return f"Successfully deleted {api_deployment_count} API deployment(s) and {api_service_count} service(s)</br> \
            {prj_deployment_count} project deployment(s) and {prj_bundle_count} bundle(s) \
            {result_string}"