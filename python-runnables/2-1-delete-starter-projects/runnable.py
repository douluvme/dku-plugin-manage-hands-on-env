# Delete starter projects (by user number, per user folder, or a whole folder), with a dry-run mode.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "delete_projects"
