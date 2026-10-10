# This file is the actual code for the Python runnable 1-2-change-owner-starter-projects
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.common_functions import *


class MyRunnable(HandsOnRunnable):
    """Set the owner of <project>_NN to userNN (or back to admin) for user99 and
    users user_num_from..user_num_to."""

    def execute(self, progress_callback):
        config = self.config
        client = self.client
        user_num_from = int(config["user_num_from"])
        user_num_to = int(config["user_num_to"])
        admin_TF = config["admin_TF"]

        total_update_count = 0
        project_key = config["project_key_select"] if config["key_select_method"] == "from_list" else config["project_key_input"]

        # 99 for instructor
        total_update_count += set_project_owner_by_num(client, project_key, '99', set_owner_to_admin_TF=admin_TF)

        for x in range(user_num_from, user_num_to + 1):
            total_update_count += set_project_owner_by_num(client, project_key, str(x).zfill(2), set_owner_to_admin_TF=admin_TF)

        return f"Successfully changed ownership for {total_update_count} project(s)"
