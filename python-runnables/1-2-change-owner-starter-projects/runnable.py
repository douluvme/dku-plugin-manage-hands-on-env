# Change the owner of one starter project's copies (KEY_99, KEY_NN ...) to each user, or back to admin.
from managehandsonenv import base
from managehandsonenv.projects import set_project_owner, suffixed_key
from managehandsonenv.users import iter_user_nums_range, user_id


class MyRunnable(base.HandsOnRunnable):
    def execute(self, progress_callback):
        config = self.config
        user_num_from = int(config["user_num_from"])
        user_num_to = int(config["user_num_to"])
        admin_TF = bool(config.get("admin_TF", False))

        project_key = (config["project_key_select"]
                       if config["key_select_method"] == "from_list"
                       else config["project_key_input"])

        total_update_count = 0
        # the instructor (user99) is always included
        for user_num in iter_user_nums_range(user_num_from, user_num_to):
            owner = "admin" if admin_TF else user_id(user_num)
            if set_project_owner(self.client, suffixed_key(project_key, user_num), owner):
                total_update_count += 1

        return "Successfully changed ownership for {} project(s)".format(total_update_count)
