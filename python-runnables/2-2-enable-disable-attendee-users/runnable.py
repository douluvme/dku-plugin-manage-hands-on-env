# This file is the actual code for the Python runnable 2-2-enable-disable-attendee-users
from managehandsonenv.base import HandsOnRunnable
import re


class MyRunnable(HandsOnRunnable):
    """Enable or disable every userNN login except the instructor (user99)."""

    def execute(self, progress_callback):
        config = self.config
        client = self.client
        enable_or_disable = config["enable_or_disable"]
        user_enabled = enable_or_disable != "disable"

        dss_users = client.list_users()
        total_update_count = 0

        for dss_user in dss_users:
            user_id = dss_user["login"]
            if re.search("^user[0-9]{2}", user_id) is not None and user_id != 'user99':
                print(f"{enable_or_disable} {user_id}")
                user = client.get_user(user_id)
                user_settings = user.get_settings()
                user_settings.enabled = user_enabled
                user_settings.save()
                total_update_count += 1
            else:
                print(f"Skip {user_id}")

        return f"Successfully {enable_or_disable}d {total_update_count} user(s)"
