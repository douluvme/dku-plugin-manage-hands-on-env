# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.common_functions import set_project_owner_by_num


class MyRunnable(HandsOnRunnable):
    """Change the owner of one starter project for a range of users (instructor always included)."""

    def execute(self, progress_callback):
        config = self.config
        client = self.client
        user_num_from = int(config["user_num_from"])
        user_num_to = int(config["user_num_to"])
        admin_TF = config["admin_TF"]

        total_update_count = 0
        project_key = (config["project_key_select"]
                       if config["key_select_method"] == "from_list"
                       else config["project_key_input"])

        # 99 for instructor
        total_update_count += set_project_owner_by_num(client, project_key, '99', set_owner_to_admin_TF=admin_TF)

        for x in range(user_num_from, user_num_to + 1):
            total_update_count += set_project_owner_by_num(client, project_key, str(x).zfill(2), set_owner_to_admin_TF=admin_TF)

        return f"Successfully changed ownership for {total_update_count} project(s)"
