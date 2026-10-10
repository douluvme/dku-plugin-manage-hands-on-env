# Remove deployed API deployments/services and project deployments/bundles, except protected ones.
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    def __init__(self, project_key, config, plugin_config):
        super().__init__(project_key, config, plugin_config)
        self.apideployer = self.client.get_apideployer()
        self.projectdeployer = self.client.get_projectdeployer()

        api_or_bundle = self.config["api_or_bundle"]
        total_progress_count = 0

        if api_or_bundle in ['api', 'both']:
            try:
                api_deployments = self.apideployer.list_deployments() or []
                api_services = self.apideployer.list_services() or []
                total_progress_count += len(api_deployments) + len(api_services)
            except Exception as e:
                print("Error getting API deployments/services: {}".format(e))

        if api_or_bundle in ['bundle', 'both']:
            try:
                project_deployments = self.projectdeployer.list_deployments() or []
                project_bundles = self.projectdeployer.list_projects() or []
                total_progress_count += len(project_deployments) + len(project_bundles)
            except Exception as e:
                print("Error getting project deployments/bundles: {}".format(e))

        self.progress_target = total_progress_count

    def get_progress_target(self):
        return (self.progress_target, 'NONE')

    def execute(self, progress_callback):
        api_or_bundle = self.config["api_or_bundle"]
        protected_prefix = self.settings.protected_bundle_prefix
        result_string = ""
        api_deployment_count = 0
        api_service_count = 0
        prj_deployment_count = 0
        prj_bundle_count = 0
        progress = 1

        if api_or_bundle in ['api', 'both']:
            deployments = self.apideployer.list_deployments()
            print("No of deployments = ", len(deployments))
            api_deployment_count = len(deployments)
            result_string = "</br>&lt;List of API deployment&gt;"

            for deployment in deployments:
                print("### Deployment ID = ", deployment.id)
                settings = deployment.get_settings()
                settings.set_enabled(enabled=False)
                settings.save(ignore_warnings=False)
                futurestate = deployment.start_update()
                futurestate.wait_for_result()

                deployment.delete(disable_first=True, ignore_pre_delete_errors=False)
                result_string = "{}</br>- {}".format(result_string, deployment.id)
                progress_callback(progress)
                progress += 1

            services = self.apideployer.list_services()
            print("No of services = ", len(services))
            api_service_count = len(services)
            result_string = "{}</br></br>&lt;List of API service&gt;".format(result_string)

            for service in services:
                print("### Service ID = ", service.id)
                service.delete()
                result_string = "{}</br>- {}".format(result_string, service.id)
                progress_callback(progress)
                progress += 1

        if api_or_bundle in ['bundle', 'both']:
            project_deployments = self.projectdeployer.list_deployments()
            print("No of project deployments = ", len(project_deployments))
            prj_deployment_count = len(project_deployments)
            result_string = "{}</br></br>&lt;List of project deployment&gt;".format(result_string)

            for deployment in project_deployments:
                if deployment.id.startswith(protected_prefix):
                    print("Skip", deployment.id)
                else:
                    print("### Project Deployment ID = ", deployment.id)
                    deployment.delete()
                    result_string = "{}</br>- {}".format(result_string, deployment.id)

                progress_callback(progress)
                progress += 1

            bundles = self.projectdeployer.list_projects()
            print("No of bundles = ", len(bundles))
            prj_bundle_count = len(bundles)
            result_string = "{}</br></br>&lt;List of project bundle&gt;".format(result_string)

            for bundle in bundles:
                if bundle.id.startswith(protected_prefix):
                    print("Skip", bundle.id)
                else:
                    print("### Project Bundle ID = ", bundle.id)
                    bundle.delete()
                    result_string = "{}</br>- {}".format(result_string, bundle.id)

                progress_callback(progress)
                progress += 1

        return "Successfully deleted {} API deployment(s) and {} service(s)</br> \
            {} project deployment(s) and {} bundle(s) \
            {}".format(api_deployment_count, api_service_count, prj_deployment_count, prj_bundle_count, result_string)
