# Enable or disable every attendee user (userNN); the instructor (user99) is never touched.
import re

from managehandsonenv import base
from managehandsonenv.users import INSTRUCTOR_NUM, user_id

ATTENDEE_LOGIN_PATTERN = re.compile(r"^user[0-9]{2}")


class MyRunnable(base.HandsOnRunnable):
    def execute(self, progress_callback):
        enable_or_disable = self.config["enable_or_disable"]
        user_enabled = enable_or_disable != "disable"
        instructor = user_id(INSTRUCTOR_NUM)

        total_update_count = 0
        for dss_user in self.client.list_users():
            login = dss_user["login"]
            if ATTENDEE_LOGIN_PATTERN.search(login) is not None and login != instructor:
                print("{} {}".format(enable_or_disable, login))
                user_settings = self.client.get_user(login).get_settings()
                user_settings.enabled = user_enabled
                user_settings.save()
                total_update_count += 1
            else:
                print("Skip {}".format(login))

        return "Successfully {}d {} user(s)".format(enable_or_disable, total_update_count)
