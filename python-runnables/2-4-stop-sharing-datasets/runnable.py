# Stop sharing the shared dataset of the read-only project with every project not in the keep list.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "stop_sharing"
