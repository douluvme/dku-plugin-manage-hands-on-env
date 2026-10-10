# Report whether the EC2 instance hosting the API node is running or stopped.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "api_node_status"
