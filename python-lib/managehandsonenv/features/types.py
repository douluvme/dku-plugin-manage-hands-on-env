"""The :class:`Feature` record shared by the registry, the macros and the webapp."""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from managehandsonenv.context import Context

ProgressCallback = Callable[[int], None]
RunFunction = Callable[[Context, Dict[str, Any], ProgressCallback], str]
ProgressTargetFunction = Callable[[Context, Dict[str, Any]], Optional[int]]


@dataclass(frozen=True)
class Feature:
    """One thing the plugin can do, callable from a macro or from the webapp.

    ``run(ctx, params, progress_callback)`` returns the HTML result (what the
    macro shows); ``progress_target(ctx, params)`` returns how many progress
    steps ``run`` will report, or ``None`` when it reports none.
    """

    id: str
    label: str
    category: str
    macro_folder: str                     # python-runnables/<folder> whose runnable.json describes the params
    run: RunFunction
    progress_target: Optional[ProgressTargetFunction] = None
    destructive: bool = False             # the webapp asks for confirmation before running
    confirm: Optional[str] = None         # the confirmation text
    description: str = ""
    menu_label: str = ""                  # short label for the webapp's left menu (defaults to label)
    menu_category: str = ""               # short section name for the webapp's left menu (defaults to category)

    @property
    def menu_label_or_label(self) -> str:
        return self.menu_label or self.label

    @property
    def menu_category_or_category(self) -> str:
        return self.menu_category or self.category

    def needs_confirmation(self, params: Dict[str, Any]) -> bool:
        """Destructive features confirm, except a delete that is only a dry run."""
        if not self.destructive:
            return False
        if "delete_TF" in params:
            return bool(params.get("delete_TF"))
        return True
