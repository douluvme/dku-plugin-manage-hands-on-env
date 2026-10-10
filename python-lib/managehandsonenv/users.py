"""Workshop user numbering and the per-user project folders under the sandbox folder."""
import re

#: The instructor is always ``user99``; attendees are ``user01`` .. ``userNN``.
INSTRUCTOR_NUM = "99"

#: A user folder directly under the sandbox folder is named exactly ``userNN``.
USER_FOLDER_PATTERN = re.compile(r"^user\d{2}$")

#: An attendee login starts with ``userNN`` (kept as a prefix match, as before).
ATTENDEE_LOGIN_PATTERN = re.compile(r"^user\d{2}")


def user_num(number):
    """Zero-padded two-digit user number: ``7 -> "07"``."""
    return str(int(number)).zfill(2)


def user_id(num):
    """Login / folder name for a user number: ``"07" -> "user07"``."""
    return f"user{num}"


def iter_user_nums(count):
    """Yield the instructor (``"99"``) then ``"01"`` .. ``"NN"`` for ``count`` attendees."""
    yield INSTRUCTOR_NUM
    for x in range(1, int(count) + 1):
        yield user_num(x)


def iter_user_nums_range(num_from, num_to):
    """Yield the instructor (``"99"``) then ``num_from`` .. ``num_to`` inclusive."""
    yield INSTRUCTOR_NUM
    for x in range(int(num_from), int(num_to) + 1):
        yield user_num(x)


def is_attendee_login(login):
    """True for ``userNN`` logins other than the instructor."""
    return ATTENDEE_LOGIN_PATTERN.match(login) is not None and login != user_id(INSTRUCTOR_NUM)


def list_user_folders(client, sandbox_folder):
    """All ``userNN`` folders directly under the sandbox folder, sorted by name."""
    sandbox = client.get_project_folder(sandbox_folder)
    folders = [
        f for f in sandbox.list_child_folders()
        if USER_FOLDER_PATTERN.match(f.get_name())
    ]
    return sorted(folders, key=lambda f: f.get_name())


def get_user_folder(client, user_login, sandbox_folder, create=False):
    """Return the user's project folder under the sandbox folder.

    Returns None when it does not exist and ``create`` is False. When created,
    the folder's owner is set to the user.
    """
    sandbox = client.get_project_folder(sandbox_folder)
    user_folder = next(
        (f for f in sandbox.list_child_folders() if f.get_name() == user_login), None
    )

    if user_folder is not None:
        print(f"{user_login}'s folder already exists")
        return user_folder

    print(f"{user_login}'s folder doesn't exist")
    if not create:
        return None

    user_folder = sandbox.create_sub_folder(user_login)
    print(f"{user_login} folder created")

    folder_settings = user_folder.get_settings()
    folder_settings.set_owner(user_login)
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
