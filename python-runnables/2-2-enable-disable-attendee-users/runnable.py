# Enable or disable every attendee user (userNN); the instructor (user99) is never touched.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "toggle_users"
