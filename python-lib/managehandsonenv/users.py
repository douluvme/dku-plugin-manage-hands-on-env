"""Workshop users and their project folders.

Attendees log in as ``user01`` .. ``userNN``; the instructor is ``user99``.
Every user owns a project folder of the same name under ``SANDBOX``.
"""
import re

SANDBOX_FOLDER = "SANDBOX"
INSTRUCTOR_NUM = "99"

# Folder names are exactly "userNN"; logins only need to start with it.
USER_FOLDER_PATTERN = re.compile(r"^user\d{2}$")
ATTENDEE_LOGIN_PATTERN = re.compile(r"^user\d{2}")


def user_id(num):
    """``"07"`` -> ``"user07"``. Accepts an int or a (zero-padded) string."""
    return f"user{str(num).zfill(2)}"


def iter_user_nums(count):
    """Yield the instructor (``"99"``) and then ``"01"`` .. ``"NN"`` for ``count`` attendees."""
    yield INSTRUCTOR_NUM
    for x in range(1, int(count) + 1):
        yield str(x).zfill(2)


def iter_user_nums_range(num_from, num_to):
    """Yield the instructor (``"99"``) and then ``num_from`` .. ``num_to`` inclusive, zero-padded."""
    yield INSTRUCTOR_NUM
    for x in range(int(num_from), int(num_to) + 1):
        yield str(x).zfill(2)


def is_attendee_login(login):
    """True for ``userNN`` logins other than the instructor."""
    return ATTENDEE_LOGIN_PATTERN.search(login) is not None and login != user_id(INSTRUCTOR_NUM)


def list_user_folders(client):
    """All ``userNN`` folders directly under SANDBOX, sorted by name."""
    sandbox = client.get_project_folder(SANDBOX_FOLDER)
    folders = [
        f for f in sandbox.list_child_folders()
        if USER_FOLDER_PATTERN.match(f.get_name())
    ]
    return sorted(folders, key=lambda f: f.get_name())


def get_user_folder(client, user, create=False):
    """Return ``user``'s project folder under SANDBOX, or None.

    With ``create=True`` a missing folder is created and ``user`` is made its owner.
    """
    sandbox = client.get_project_folder(SANDBOX_FOLDER)
    user_folder = next(
        (f for f in sandbox.list_child_folders() if f.get_name() == user), None
    )

    if user_folder is not None:
        print(f"{user}'s folder already exists")
        return user_folder

    print(f"{user}'s folder doesn't exist")
    if not create:
        return None

    user_folder = sandbox.create_sub_folder(user)
    print(f"{user} folder created")

    folder_settings = user_folder.get_settings()
    folder_settings.set_owner(user)
    folder_settings.save()

    return user_folder


def walk_folder_tree(folder, depth=0):
    """
    Depth-first, deepest first. Yields (folder, depth, project_keys).
    Ordering guarantees children are yielded before their parent,
    so deleting in iteration order is always safe.
    """
    for child in folder.list_child_folders():
        for item in walk_folder_tree(child, depth + 1):
            yield item
    yield folder, depth, folder.list_project_keys()
