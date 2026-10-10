# Change the owner of every project directly in the sandbox folder to admin.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "sandbox_to_admin"
