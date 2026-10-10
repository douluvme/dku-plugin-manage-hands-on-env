"""Load every macro the way DSS does (by file) and exercise the ones that need no AWS."""
import pytest
from conftest import load_runnable, runnable_dirs
from fakes import FakeClient

from managehandsonenv.base import HandsOnRunnable, Settings
from managehandsonenv.starters import STARTERS

STARTER_MACROS = {
    "1-1-duplicate-starter-projects",
    "1-2-change-owner-starter-projects",
    "2-1-delete-starter-projects",
}


def folder_named(name):
    return next(p for p in runnable_dirs() if p.name == name)


@pytest.mark.parametrize("folder", runnable_dirs(), ids=lambda p: p.name)
def test_every_runnable_defines_myrunnable(folder):
    module = load_runnable(folder)
    assert issubclass(module.MyRunnable, HandsOnRunnable)
    assert module.MyRunnable.execute is not HandsOnRunnable.execute, "execute() must be overridden"
    if folder.name in STARTER_MACROS:
        assert module.do({"parameterName": "x"}, {}, {}, {}) == {"choices": STARTERS}
    else:
        assert not hasattr(module, "do")


def test_runnable_dirs_are_the_expected_eleven():
    assert len(runnable_dirs()) == 11  # 12 before the [OLD] duplicate was removed
    assert not any("[OLD]" in p.name for p in runnable_dirs())


def test_guard_refuses_other_projects(fake_client):
    module = load_runnable(folder_named("1-3-change-owner-root-projects-to-admin"))
    runnable = module.MyRunnable("SOMEPROJECT", {}, {})
    with pytest.raises(RuntimeError, match="ADMINV4"):
        runnable.run(lambda p: None)
    assert fake_client.calls == []


def test_guard_honours_plugin_setting(fake_client):
    fake_client.build({"SANDBOX": ["A"]})
    module = load_runnable(folder_named("1-3-change-owner-root-projects-to-admin"))
    runnable = module.MyRunnable("MYADMIN", {}, {"admin_project_key": "MYADMIN"})
    out = runnable.run(lambda p: None)
    assert "changed owner of 1 project(s)" in out
    assert ("set_permissions", "A", "admin") in fake_client.calls


def test_settings_from_plugin_config():
    assert Settings.from_plugin_config(None) == Settings()
    custom = Settings.from_plugin_config({"aws_region": " eu-west-1 ", "sandbox_folder": "", "rds_instance_id": None})
    assert custom.aws_region == "eu-west-1"
    assert custom.sandbox_folder == "SANDBOX"
    assert custom.rds_instance_id == "postgres-mag"
    assert custom.api_node_instance_id == "i-0e7ccb12c93ac1df2"


def test_aws_preset_prefers_plugin_config(fake_client):
    module = load_runnable(folder_named("3-2-get-db-class"))
    macro_preset = {"aws_access_key_id": "macro", "aws_secret_access_key": "s"}
    plugin_preset = {"aws_access_key_id": "plugin", "aws_secret_access_key": "s"}
    assert module.MyRunnable("ADMINV4", {"aws_account": macro_preset}, {"aws_account": plugin_preset}).aws_preset() is plugin_preset
    assert module.MyRunnable("ADMINV4", {"aws_account": macro_preset}, {"aws_account": {}}).aws_preset() is macro_preset
    assert module.MyRunnable("ADMINV4", {}, {}).aws_preset() == {}


def test_change_owner_macro(fake_client):
    fake_client.build({"SANDBOX/user99": ["KO1COBUILD_99"], "SANDBOX/user01": ["KO1COBUILD_01"], "SANDBOX/user02": []})
    module = load_runnable(folder_named("1-2-change-owner-starter-projects"))
    config = {"user_num_from": 1, "user_num_to": 2, "key_select_method": "from_list",
              "project_key_select": "KO1COBUILD", "admin_TF": False}
    out = module.MyRunnable("ADMINV4", config, {}).run(lambda p: None)
    assert out == "Successfully changed ownership for 2 project(s)"  # KO1COBUILD_02 does not exist
    assert fake_client.projects["KO1COBUILD_99"].permissions["owner"] == "user99"
    assert fake_client.projects["KO1COBUILD_01"].permissions["owner"] == "user01"


def test_duplicate_macro(fake_client):
    fake_client.build({"ROOT": ["KO1COBUILD", "KO2EXPL"], "SANDBOX/user01": ["KO2EXPL_01"]})
    module = load_runnable(folder_named("1-1-duplicate-starter-projects"))
    config = {"user_count": 1, "key_select_method": "from_list", "project_keys_list": ["KO1COBUILD", "KO2EXPL"]}
    runnable = module.MyRunnable("ADMINV4", config, {})
    assert runnable.get_progress_target() == (4, "NONE")

    progress = []
    out = runnable.run(progress.append)

    assert out.startswith("<h4>Successfully duplicated 3 project(s)</h4>")
    assert "<br/><b>user99</b> : &lt;KO1COBUILD_99&gt; &lt;KO2EXPL_99&gt;" in out
    assert "<br/><b>user01</b> : &lt;KO1COBUILD_01&gt;" in out
    assert "<h4>1 skipped (already exist)</h4><ul><li>&lt;KO2EXPL_01&gt;</li></ul>" in out
    assert "failure" not in out
    assert fake_client.get_project_folder("user99").list_project_keys() == ["KO1COBUILD_99", "KO2EXPL_99"]
    assert fake_client.get_project_folder("user01").list_project_keys() == ["KO2EXPL_01", "KO1COBUILD_01"]
    assert fake_client.get_project_folder("user99").owner == "user99"
    assert progress == [1, 2, 3, 4]


DELETE_TREE = {
    "ROOT": ["ADMINV4"],
    "SANDBOX": ["SBX", "KEEP"],
    "SANDBOX/user99": ["KO1COBUILD_99"],
    "SANDBOX/user01": ["KO1COBUILD_01", "OWN_01"],
    "SANDBOX/user01/work": ["WORK_01"],
}

DELETE_CONFIGS = {
    "user_num": {"user_count": 1, "key_select_method": "from_list", "project_keys_list": ["KO1COBUILD"]},
    "all_user_folders": {"projects_to_keep": ["OWN_01"]},
    "sandbox": {"projects_to_keep": ["KEEP"]},
}


@pytest.mark.parametrize("delete_type", sorted(DELETE_CONFIGS))
def test_delete_macro_dry_run_matches_real_run(monkeypatch, delete_type):
    import sys

    module = load_runnable(folder_named("2-1-delete-starter-projects"))
    outputs = {}
    clients = {}
    for delete_TF in (False, True):
        client = FakeClient().build(DELETE_TREE)
        clients[delete_TF] = client
        monkeypatch.setattr(sys.modules["dataiku"], "api_client", lambda c=client: c)
        config = dict(DELETE_CONFIGS[delete_type], delete_type=delete_type, delete_TF=delete_TF)
        runnable = module.MyRunnable("ADMINV4", config, {})
        assert runnable.get_progress_target() == (max(len(runnable.targets), 1), "NONE")
        outputs[delete_TF] = runnable.run(lambda p: None)

    dry, real = outputs[False], outputs[True]
    assert dry.startswith("<h4>Identified ")
    assert real.startswith("<h4>Successfully deleted ")
    # same body once the verbs are normalised
    def normalise(text):
        for verb in ("Identified ", " to delete", "Successfully deleted ", "Deleted "):
            text = text.replace(verb, "")
        return text

    assert normalise(dry) == normalise(real)
    assert "failure" not in real
    assert clients[False].calls == []
    assert clients[True].deleted_projects() or clients[True].deleted_folders()


def test_delete_macro_renders_user_num_mode(fake_client):
    fake_client.build(DELETE_TREE)
    module = load_runnable(folder_named("2-1-delete-starter-projects"))
    config = dict(DELETE_CONFIGS["user_num"], delete_type="user_num", delete_TF=True)
    out = module.MyRunnable("ADMINV4", config, {}).run(lambda p: None)
    assert out == (
        "<h4>Successfully deleted 2 project(s)</h4>"
        "<br/><b>user99</b> : &lt;KO1COBUILD_99&gt; <i>[+user99]</i>"
        "<br/><b>user01</b> : &lt;KO1COBUILD_01&gt; <i>[+user01]</i>"
        "<h4>Deleted 2 user folder(s)</h4>"
    )
    assert fake_client.deleted_projects() == ["KO1COBUILD_99", "KO1COBUILD_01"]
    assert fake_client.deleted_folders() == ["SANDBOX/user99", "SANDBOX/user01"]
    # DSS moves the remaining content of a deleted folder to its parent; OWN_01 survives
    assert "OWN_01" in fake_client.projects


def test_delete_macro_renders_sandbox_mode(fake_client):
    fake_client.build(DELETE_TREE)
    module = load_runnable(folder_named("2-1-delete-starter-projects"))
    config = dict(DELETE_CONFIGS["sandbox"], delete_type="sandbox", delete_TF=False)
    out = module.MyRunnable("ADMINV4", config, {}).run(lambda p: None)
    assert out == "<h4>Identified 1 project(s) to delete</h4>&lt;SBX&gt;<br/><h4>Identified 0 user folder(s)</h4>"
    assert fake_client.calls == []


def test_delete_macro_all_user_folders_keeps_parent_of_kept_project(fake_client):
    fake_client.build(DELETE_TREE)
    module = load_runnable(folder_named("2-1-delete-starter-projects"))
    config = dict(DELETE_CONFIGS["all_user_folders"], delete_type="all_user_folders", delete_TF=True)
    out = module.MyRunnable("ADMINV4", config, {}).run(lambda p: None)
    assert out == (
        "<h4>Successfully deleted 3 project(s)</h4>"
        "<br/><b>user01</b> : &lt;WORK_01&gt; <i>[+user01/work]</i> &lt;KO1COBUILD_01&gt;"
        "<br/><b>user99</b> : &lt;KO1COBUILD_99&gt; <i>[+user99]</i>"
        "<h4>Deleted 2 user folder(s)</h4>"
    )
    assert "OWN_01" in fake_client.projects
    assert fake_client.get_project_folder("user01").list_project_keys() == ["OWN_01"]
