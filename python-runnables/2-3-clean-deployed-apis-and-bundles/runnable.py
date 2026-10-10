# Remove deployed API deployments/services and project deployments/bundles, except protected ones.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "clean_deployments"
