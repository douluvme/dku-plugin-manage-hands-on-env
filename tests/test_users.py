from fakes import FakeClient

from managehandsonenv.users import (
    INSTRUCTOR_NUM,
    format_user_num,
    get_user_folder,
    iter_user_nums,
    iter_user_nums_range,
    list_user_folders,
    user_id,
    walk_folder_tree,
)


def test_iter_user_nums_instructor_first_then_zero_padded():
    assert list(iter_user_nums(3)) == ["99", "01", "02", "03"]


def test_iter_user_nums_zero_users_yields_only_instructor():
    assert list(iter_user_nums(0)) == [INSTRUCTOR_NUM]


def test_iter_user_nums_two_digit_numbers_and_padding():
    nums = list(iter_user_nums(12))
    assert nums[0] == "99"
    assert nums[1:] == ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    assert all(len(n) == 2 for n in nums)


def test_iter_user_nums_accepts_float_count_from_json():
    assert list(iter_user_nums(2.0)) == ["99", "01", "02"]


def test_iter_user_nums_range():
    assert list(iter_user_nums_range(2, 4)) == ["99", "02", "03", "04"]
    assert list(iter_user_nums_range(2, 4, include_instructor=False)) == ["02", "03", "04"]
    assert list(iter_user_nums_range(5, 4)) == ["99"]


def test_user_id_and_format():
    assert user_id("01") == "user01"
    assert format_user_num(7) == "07"
    assert user_id(format_user_num(99)) == "user99"


def test_list_user_folders_filters_and_sorts():
    client = FakeClient().build({
        "SANDBOX/user02": [],
        "SANDBOX/other": [],
        "SANDBOX/user99": [],
        "SANDBOX/user1": [],
        "SANDBOX/user01": [],
        "SANDBOX/user001": [],
    })
    assert [f.get_name() for f in list_user_folders(client, "SANDBOX")] == ["user01", "user02", "user99"]


def test_get_user_folder_existing_and_missing():
    client = FakeClient().build({"SANDBOX/user01": []})
    assert get_user_folder(client, "user01", sandbox_folder="SANDBOX").get_name() == "user01"
    assert get_user_folder(client, "user02", sandbox_folder="SANDBOX") is None
    assert client.calls == []


def test_get_user_folder_create_sets_owner():
    client = FakeClient().build({"SANDBOX": []})
    folder = get_user_folder(client, "user05", create=True, sandbox_folder="SANDBOX")
    assert folder.get_name() == "user05"
    assert folder.owner == "user05"
    assert folder.parent.get_name() == "SANDBOX"
    assert ("create_sub_folder", "SANDBOX", "user05") in client.calls
    assert ("save_folder_settings", "SANDBOX/user05", "user05") in client.calls


def test_walk_folder_tree_is_deepest_first():
    client = FakeClient().build({
        "SANDBOX/user01": ["A"],
        "SANDBOX/user01/work": ["B"],
        "SANDBOX/user01/work/deep": [],
        "SANDBOX/user01/empty": [],
    })
    walked = [(f.path, depth, keys) for f, depth, keys in walk_folder_tree(client.get_project_folder("user01"))]
    assert walked == [
        ("SANDBOX/user01/work/deep", 2, []),
        ("SANDBOX/user01/work", 1, ["B"]),
        ("SANDBOX/user01/empty", 1, []),
        ("SANDBOX/user01", 0, ["A"]),
    ]
