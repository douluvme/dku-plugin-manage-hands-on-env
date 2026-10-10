# Report the current RDS DB instance class and status of the workshop database.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "db_status"
