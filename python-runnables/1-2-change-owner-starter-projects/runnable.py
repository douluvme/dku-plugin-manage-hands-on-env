# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.projects import set_project_owner, suffixed_key
from managehandsonenv.users import iter_user_nums_range, user_id


class MyRunnable(HandsOnRunnable):
    """Change the owner of one starter project for a range of users (instructor always included)."""

    def execute(self, progress_callback):
        config = self.config
        client = self.client
        user_num_from = int(config["user_num_from"])
        user_num_to = int(config["user_num_to"])
        admin_TF = config["admin_TF"]

        project_key = (config["project_key_select"]
                       if config["key_select_method"] == "from_list"
                       else config["project_key_input"])

        total_update_count = 0

        # the instructor (user99) is always included
        for num in iter_user_nums_range(user_num_from, user_num_to):
            owner = 'admin' if admin_TF else user_id(num)
            if set_project_owner(client, suffixed_key(project_key, num), owner):
                total_update_count += 1

        return f"Successfully changed ownership for {total_update_count} project(s)"
