"""Workshop user numbering and the per-user project folders under the sandbox folder.

Users are ``user01`` .. ``userNN`` for attendees and ``user99`` for the instructor.
"""
import re
from typing import Iterator, List, Optional, Tuple

INSTRUCTOR_NUM = "99"
USER_FOLDER_PATTERN = re.compile(r"^user\d{2}$")


def format_user_num(number: int) -> str:
    """``1`` -> ``"01"``."""
    return str(int(number)).zfill(2)


def user_id(user_num: str) -> str:
    """``"01"`` -> ``"user01"``."""
    return "user" + user_num


def iter_user_nums(user_count: int) -> Iterator[str]:
    """Yield the instructor (``"99"``) first, then ``"01"`` .. ``"NN"``."""
    yield INSTRUCTOR_NUM
    for number in range(1, int(user_count) + 1):
        yield format_user_num(number)


def iter_user_nums_range(user_num_from: int, user_num_to: int, include_instructor: bool = True) -> Iterator[str]:
    """Yield the instructor (optional) then every number from ``user_num_from`` to ``user_num_to`` inclusive."""
    if include_instructor:
        yield INSTRUCTOR_NUM
    for number in range(int(user_num_from), int(user_num_to) + 1):
        yield format_user_num(number)


def list_user_folders(client, sandbox_folder: str = "SANDBOX") -> List:
    """All ``userNN`` folders directly under the sandbox folder, sorted by name."""
    sandbox = client.get_project_folder(sandbox_folder)
    folders = [f for f in sandbox.list_child_folders() if USER_FOLDER_PATTERN.match(f.get_name())]
    return sorted(folders, key=lambda f: f.get_name())


def get_user_folder(client, user: str, create: bool = False, sandbox_folder: str = "SANDBOX"):
    """Return the user's project folder under the sandbox folder, or None.

    With ``create=True`` the folder is created (owned by the user) when missing.
    """
    sandbox = client.get_project_folder(sandbox_folder)
    folder = next((f for f in sandbox.list_child_folders() if f.get_name() == user), None)

    if folder is not None:
        print("{}'s folder already exists".format(user))
        return folder

    print("{}'s folder doesn't exist".format(user))
    if not create:
        return None

    folder = sandbox.create_sub_folder(user)
    print("{} folder created".format(user))

    folder_settings = folder.get_settings()
    folder_settings.set_owner(user)
    folder_settings.save()
    return folder


def walk_folder_tree(folder, depth: int = 0) -> Iterator[Tuple[object, int, List[str]]]:
    """Depth-first, deepest first. Yields ``(folder, depth, project_keys)``.

    Children are yielded before their parent, so deleting in iteration order is safe.
    """
    for child in folder.list_child_folders():
        for item in walk_folder_tree(child, depth + 1):
            yield item
    yield folder, depth, folder.list_project_keys()


def find_child_folder(folder, name: str) -> Optional[object]:
    """The direct child folder called ``name``, or None."""
    return next((f for f in folder.list_child_folders() if f.get_name() == name), None)
