"""Registry of everything the plugin can do.

A :class:`~managehandsonenv.features.types.Feature` is callable from a macro
(``HandsOnRunnable`` delegates to it by ``feature_id``) and from the webapp
(which builds a form from the feature's macro descriptor and runs it as a
background job). Add a feature here and both front ends pick it up.
"""
from collections import OrderedDict
from typing import Dict, List, Tuple

from managehandsonenv.features import housekeeping, infra, setup
from managehandsonenv.features.types import Feature  # noqa: F401  (re-exported)


class FeatureNotFound(KeyError):
    pass


FEATURES: "OrderedDict[str, Feature]" = OrderedDict(
    (feature.id, feature) for module in (setup, housekeeping, infra) for feature in module.FEATURES
)


def get_feature(feature_id: str) -> Feature:
    try:
        return FEATURES[feature_id]
    except KeyError:
        raise FeatureNotFound("Unknown feature {!r} (known: {})".format(feature_id, list(FEATURES)))


def by_category() -> List[Tuple[str, List[Feature]]]:
    """``[(category, [features...]), ...]`` in registration order, for the button bar."""
    groups: Dict[str, List[Feature]] = OrderedDict()
    for feature in FEATURES.values():
        groups.setdefault(feature.category, []).append(feature)
    return list(groups.items())


def feature_for_macro(macro_folder: str) -> Feature:
    """The feature backing ``python-runnables/<macro_folder>``."""
    for feature in FEATURES.values():
        if feature.macro_folder == macro_folder:
            return feature
    raise FeatureNotFound("No feature is registered for macro folder {!r}".format(macro_folder))
