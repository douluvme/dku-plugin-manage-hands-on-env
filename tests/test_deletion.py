import pytest
from fakes import FakeClient

from managehandsonenv.base import Settings
from managehandsonenv.deletion import (
    FOLDER,
    PROJECT,
    AllUserFolders,
    ByUserNum,
    WholeFolder,
    apply,
    build_plan,
)

RUNNING = "ADMINV4"
SETTINGS = Settings()

TREE = {
    "ROOT": ["ADMINV4", "READONLY"],
    "SANDBOX": ["SBX1", "KEEPME"],
    "SANDBOX/user99": ["KO1COBUILD_99", "KO2EXPL_99"],
    "SANDBOX/user01": ["KO1COBUILD_01", "OWN_01"],
    "SANDBOX/user01/work": ["WORK_01"],
    "SANDBOX/user01/empty": [],
    "SANDBOX/user02": ["KO1COBUILD_02"],
    "SANDBOX/user02/sub": ["KEEPME3"],
    "SANDBOX/user02/sub/deep": [],
    "SANDBOX/user03": [],
    "SANDBOX/other": ["OTHER"],
}


def make_client():
    return FakeClient().build(TREE)


def summary(targets):
    """``[(kind, key, keep), ...]`` for readable assertions."""
    return [(t.kind, t.key, t.keep) for t in targets]


# --- ByUserNum -----------------------------------------------------------------

def test_by_user_num_targets_existing_projects_then_folder_per_user():
    config = {"delete_type": "user_num", "user_count": 2, "key_select_method": "from_list",
              "project_keys_list": ["KO1COBUILD", "KO2EXPL"]}
    targets = ByUserNum(make_client(), SETTINGS, config, RUNNING).targets()
    assert summary(targets) == [
        (PROJECT, "KO1COBUILD_99", False),
        (PROJECT, "KO2EXPL_99", False),
        (FOLDER, "user99", False),
        (PROJECT, "KO1COBUILD_01", False),   # KO2EXPL_01 does not exist: not a target
        (FOLDER, "user01", False),
        (PROJECT, "KO1COBUILD_02", False),
        (FOLDER, "user02", False),
    ]
    assert [t.group for t in targets] == ["user99", "user99", "user99", "user01", "user01", "user02", "user02"]
    folder = next(t for t in targets if t.key == "user01")
    assert folder.depends_on == ("KO1COBUILD_01",)
    assert folder.handle.get_name() == "user01"


def test_by_user_num_skips_missing_folder_and_uses_input_keys():
    client = make_client()
    config = {"delete_type": "user_num", "user_count": 4, "key_select_method": "from_input",
              "project_keys_input": ["OWN"]}
    targets = ByUserNum(client, SETTINGS, config, RUNNING).targets()
    # user99: nothing exists but the folder; user03: folder only; user04: nothing at all
    assert summary(targets) == [
        (FOLDER, "user99", False),
        (PROJECT, "OWN_01", False),
        (FOLDER, "user01", False),
        (FOLDER, "user02", False),
        (FOLDER, "user03", False),
    ]


# --- AllUserFolders ------------------------------------------------------------

def test_all_user_folders_targets_with_keep_list_and_nested_folders():
    config = {"delete_type": "all_user_folders", "projects_to_keep": ["KEEPME3", "KEEPME"]}
    targets = AllUserFolders(make_client(), SETTINGS, config, RUNNING).targets()
    assert summary(targets) == [
        # user01: children first (deepest first), then its projects, then itself
        (PROJECT, "WORK_01", False),
        (FOLDER, "user01/work", False),
        (FOLDER, "user01/empty", False),          # nested empty folder is deleted
        (PROJECT, "KO1COBUILD_01", False),
        (PROJECT, "OWN_01", False),
        (FOLDER, "user01", False),
        # user02: deep is empty -> deleted; sub keeps KEEPME3 -> kept; user02 kept because sub is kept
        (FOLDER, "user02/sub/deep", False),
        (PROJECT, "KEEPME3", True),
        (FOLDER, "user02/sub", True),
        (PROJECT, "KO1COBUILD_02", False),
        (FOLDER, "user02", True),
        # user03: no projects at all -> folder deleted
        (FOLDER, "user03", False),
        # user99
        (PROJECT, "KO1COBUILD_99", False),
        (PROJECT, "KO2EXPL_99", False),
        (FOLDER, "user99", False),
    ]
    # "other" and projects directly in SANDBOX are never touched
    assert "OTHER" not in [t.key for t in targets]
    assert "SBX1" not in [t.key for t in targets]

    by_key = {(t.kind, t.key): t for t in targets}
    assert by_key[(FOLDER, "user01")].depends_on == ("user01/work", "user01/empty", "KO1COBUILD_01", "OWN_01")
    assert by_key[(FOLDER, "user01/work")].depth == 1
    assert by_key[(FOLDER, "user02/sub/deep")].depth == 2
    assert by_key[(FOLDER, "user02")].group == "user02"


def test_all_user_folders_running_project_is_kept():
    client = FakeClient().build({"SANDBOX/user01": ["ADMINV4", "X"]})
    targets = AllUserFolders(client, SETTINGS, {"delete_type": "all_user_folders"}, RUNNING).targets()
    assert summary(targets) == [(PROJECT, "ADMINV4", True), (PROJECT, "X", False), (FOLDER, "user01", True)]


# --- WholeFolder ---------------------------------------------------------------

def test_whole_folder_sandbox_and_root():
    config = {"delete_type": "sandbox", "projects_to_keep": ["KEEPME"]}
    targets = WholeFolder(make_client(), SETTINGS, config, RUNNING).targets()
    assert summary(targets) == [(PROJECT, "SBX1", False), (PROJECT, "KEEPME", True)]
    assert all(t.group == "" for t in targets)

    config = {"delete_type": "root_folder", "projects_to_keep": []}
    targets = WholeFolder(make_client(), SETTINGS, config, RUNNING).targets()
    assert summary(targets) == [(PROJECT, "ADMINV4", True), (PROJECT, "READONLY", False)]


def test_build_plan_dispatch_and_unknown_type():
    client = make_client()
    assert isinstance(build_plan(client, SETTINGS, {"delete_type": "user_num"}, RUNNING), ByUserNum)
    assert isinstance(build_plan(client, SETTINGS, {"delete_type": "all_user_folders"}, RUNNING), AllUserFolders)
    assert isinstance(build_plan(client, SETTINGS, {"delete_type": "sandbox"}, RUNNING), WholeFolder)
    assert isinstance(build_plan(client, SETTINGS, {"delete_type": "root_folder"}, RUNNING), WholeFolder)
    with pytest.raises(ValueError):
        build_plan(client, SETTINGS, {"delete_type": "everything"}, RUNNING)
    with pytest.raises(ValueError):
        build_plan(client, SETTINGS, {}, RUNNING)


# --- apply ---------------------------------------------------------------------

CONFIGS = [
    {"delete_type": "user_num", "user_count": 2, "key_select_method": "from_list",
     "project_keys_list": ["KO1COBUILD", "KO2EXPL"]},
    {"delete_type": "all_user_folders", "projects_to_keep": ["KEEPME3"]},
    {"delete_type": "sandbox", "projects_to_keep": ["KEEPME"]},
    {"delete_type": "root_folder", "projects_to_keep": []},
]


@pytest.mark.parametrize("config", CONFIGS, ids=[c["delete_type"] for c in CONFIGS])
def test_apply_dry_run_and_real_run_report_the_same_set(config):
    dry_client, real_client = make_client(), make_client()
    dry_targets = build_plan(dry_client, SETTINGS, config, RUNNING).targets()
    real_targets = build_plan(real_client, SETTINGS, config, RUNNING).targets()
    assert summary(dry_targets) == summary(real_targets)

    dry = apply(dry_targets, dry_client, dry_run=True)
    real = apply(real_targets, real_client, dry_run=False)

    assert dry.done_keys() == real.done_keys()
    assert [t.key for t in dry.done] == [t.key for t in real.done]
    assert summary(dry.kept) == summary(real.kept)
    assert dry.failures == real.failures == []

    # dry run touched nothing
    assert dry_client.calls == []
    assert set(dry_client.projects) == set(make_client().projects)

    # real run deleted exactly the reported projects and folders, in order
    assert real_client.deleted_projects() == [t.key for t in real.projects]
    assert real_client.deleted_folders() == ["SANDBOX/" + t.key for t in real.folders]
    for target in real.projects:
        assert target.key not in real_client.projects
    for target in real.kept:
        if target.kind == PROJECT:
            assert target.key in real_client.projects


def test_apply_progress_callback_counts_every_target():
    client = make_client()
    targets = build_plan(client, SETTINGS, CONFIGS[1], RUNNING).targets()
    seen = []
    apply(targets, client, dry_run=True, progress_callback=seen.append)
    assert seen == list(range(1, len(targets) + 1))


def test_apply_failed_project_blocks_its_folders_and_parents():
    client = make_client()
    client.fail.add("WORK_01")
    targets = build_plan(client, SETTINGS, CONFIGS[1], RUNNING).targets()

    result = apply(targets, client, dry_run=False)

    assert [t.key for t in result.projects] == ["KO1COBUILD_01", "OWN_01", "KO1COBUILD_02", "KO1COBUILD_99", "KO2EXPL_99"]
    assert [t.key for t in result.folders] == ["user01/empty", "user02/sub/deep", "user03", "user99"]
    assert [key for key, _ in result.failures] == ["WORK_01", "user01/work", "user01"]
    assert "WORK_01" in result.failures[1][1]
    assert "user01/work" in result.failures[2][1]
    # the blocked folders were never asked to delete themselves
    assert "SANDBOX/user01/work" not in client.deleted_folders()
    assert "SANDBOX/user01" not in client.deleted_folders()
    assert "WORK_01" in client.projects


def test_apply_user_num_folder_skipped_when_project_fails():
    client = make_client()
    client.fail.add("KO1COBUILD_01")
    targets = build_plan(client, SETTINGS, CONFIGS[0], RUNNING).targets()
    result = apply(targets, client, dry_run=False)
    assert [key for key, _ in result.failures] == ["KO1COBUILD_01", "user01"]
    assert client.deleted_folders() == ["SANDBOX/user99", "SANDBOX/user02"]
