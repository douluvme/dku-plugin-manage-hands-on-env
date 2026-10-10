# This file is the actual code for the Python runnable 1-2-change-owner-starter-projects
from managehandsonenv import base
from managehandsonenv.users import iter_user_nums_range, user_id
from managehandsonenv.projects import suffixed_key, set_project_owner


class MyRunnable(base.HandsOnRunnable):
    """Set the owner of <project>_NN to userNN (or back to admin) for user99 and
    users user_num_from..user_num_to."""

    def execute(self, progress_callback):
        config = self.config
        client = self.client
        admin_TF = config["admin_TF"]

        project_key = (config["project_key_select"]
                       if config["key_select_method"] == "from_list"
                       else config["project_key_input"])

        total_update_count = 0

        # the instructor (99) is always included
        for user_num in iter_user_nums_range(config["user_num_from"], config["user_num_to"]):
            owner = 'admin' if admin_TF else user_id(user_num)
            if set_project_owner(client, suffixed_key(project_key, user_num), owner):
                total_update_count += 1

        return f"Successfully changed ownership for {total_update_count} project(s)"
