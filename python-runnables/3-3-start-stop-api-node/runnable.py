# Start or stop the EC2 instance hosting the API node.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "api_node_power"
