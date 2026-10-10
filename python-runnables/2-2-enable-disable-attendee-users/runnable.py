# This file is the actual code for the Python runnable manage-starter-project
from managehandsonenv.base import HandsOnRunnable
from managehandsonenv.users import is_attendee_login


class MyRunnable(HandsOnRunnable):
    """Enable or disable every attendee login (userNN), leaving the instructor (user99) untouched."""

    def execute(self, progress_callback):
        config = self.config
        client = self.client
        enable_or_disable = config["enable_or_disable"]
        user_enabled = enable_or_disable != "disable"

        dss_users = client.list_users()
        total_update_count = 0

        for dss_user in dss_users:
            login = dss_user["login"]
            if is_attendee_login(login):
                print(f"{enable_or_disable} {login}")
                user = client.get_user(login)
                user_settings = user.get_settings()
                user_settings.enabled = user_enabled
                user_settings.save()
                total_update_count += 1
            else:
                print(f"Skip {login}")

        return f"Successfully {enable_or_disable}d {total_update_count} user(s)"
