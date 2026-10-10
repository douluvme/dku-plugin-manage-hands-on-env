# Duplicate the selected starter projects once per workshop user (instructor user99 first).
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "duplicate_starters"
