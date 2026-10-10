# Change the owner of one starter project's copies (KEY_99, KEY_NN ...) to each user, or back to admin.
# The logic lives in managehandsonenv.features (shared with the plugin webapp).
from managehandsonenv import base


class MyRunnable(base.HandsOnRunnable):
    feature_id = "change_owner"
