"""The feature registry and the features that need no AWS, run through a Context + FakeClient."""
import pytest
from conftest import ROOT
from fakes import FakeClient

from managehandsonenv.context import Context
from managehandsonenv.descriptors import load_descriptor
from managehandsonenv.features import FEATURES, FeatureNotFound, by_category, feature_for_macro, get_feature
from managehandsonenv.features.types import Feature
from managehandsonenv.settings import Settings


def make_context(tree=None, project_key="ADMINV4", **settings):
    client = FakeClient().build(tree or {})
    return Context(client=client, settings=Settings(**settings), project_key=project_key)


# --- registry ------------------------------------------------------------------

def test_registry_matches_the_macro_descriptors():
    """Labels, categories and descriptions are defined in Python; the descriptors must agree."""
    for feature in FEATURES.values():
        meta = load_descriptor(ROOT / "python-runnables" / feature.macro_folder / "runnable.json")["meta"]
        assert feature.label == meta["label"], feature.id
        assert feature.category == meta["category"], feature.id
        assert feature.description == meta["description"], feature.id


def test_registry_lookups():
    assert list(FEATURES) == [
        "duplicate_starters", "change_owner", "sandbox_to_admin",
        "delete_projects", "toggle_users", "clean_deployments", "stop_sharing",
        "modify_db_class", "db_status", "api_node_power", "api_node_status",
    ]
    assert get_feature("db_status").macro_folder == "3-2-get-db-class"
    assert feature_for_macro("2-1-delete-starter-projects").id == "delete_projects"
    with pytest.raises(FeatureNotFound):
        get_feature("nope")
    with pytest.raises(FeatureNotFound):
        feature_for_macro("nope")

    categories = by_category()
    assert [name for name, _ in categories] == [
        "⚠️ Hands-on 1: Manage Starter Projects",
        "⚠️ Hands-on 2: Housekeeping",
        "⚠️ Hands-on 3: Manage Workshop Environment",
    ]
    assert [len(features) for _, features in categories] == [3, 4, 4]


def test_destructive_features_confirm_except_dry_runs():
    assert {f.id for f in FEATURES.values() if f.destructive} == {
        "delete_projects", "toggle_users", "clean_deployments", "stop_sharing", "modify_db_class", "api_node_power",
    }
    assert all(f.confirm for f in FEATURES.values() if f.destructive)
    delete = get_feature("delete_projects")
    assert delete.needs_confirmation({"delete_TF": True})
    assert not delete.needs_confirmation({"delete_TF": False})
    assert delete.needs_confirmation({})  # unknown flag: stay on the safe side
    assert get_feature("toggle_users").needs_confirmation({})
    assert not get_feature("db_status").needs_confirmation({})


def test_context_aws_preset_and_admin_check():
    ctx = make_context(project_key="OTHER")
    assert not ctx.is_admin_project
    assert ctx.aws_preset({"aws_account": {"aws_access_key_id": "macro"}}) == {"aws_access_key_id": "macro"}
    ctx.plugin_config["aws_account"] = {"aws_access_key_id": "plugin"}
    assert ctx.aws_preset({"aws_account": {"aws_access_key_id": "macro"}}) == {"aws_access_key_id": "plugin"}
    assert make_context(project_key="MYADMIN", admin_project_key="MYADMIN").is_admin_project


# --- setup features --------------------------------------------------------------

def test_duplicate_starters(capsys):
    ctx = make_context({"ROOT": ["KO1COBUILD", "KO2EXPL"], "SANDBOX/user01": ["KO2EXPL_01"]})
    feature = get_feature("duplicate_starters")
    params = {"user_count": 1, "key_select_method": "from_list", "project_keys_list": ["KO1COBUILD", "KO2EXPL"]}
    assert feature.progress_target(ctx, params) == 4

    progress = []
    out = feature.run(ctx, params, progress.append)

    assert out.startswith("<h4>Successfully duplicated 3 project(s)</h4>")
    assert "<br/><b>user99</b> : &lt;KO1COBUILD_99&gt; &lt;KO2EXPL_99&gt;" in out
    assert "<br/><b>user01</b> : &lt;KO1COBUILD_01&gt;" in out
    assert "<h4>1 skipped (already exist)</h4><ul><li>&lt;KO2EXPL_01&gt;</li></ul>" in out
    assert "failure" not in out
    assert progress == [1, 2, 3, 4]
    assert ctx.client.get_project_folder("user99").list_project_keys() == ["KO1COBUILD_99", "KO2EXPL_99"]
    assert "Skip KO2EXPL_01 (already exists)" in capsys.readouterr().out


def test_duplicate_starters_logs_through_the_context():
    lines = []
    ctx = make_context({"ROOT": ["KO1COBUILD"]})
    ctx.log = lines.append
    get_feature("duplicate_starters").run(ctx, {"user_count": 0, "key_select_method": "from_input",
                                                "project_keys_input": ["KO1COBUILD"]}, lambda p: None)
    assert lines[:2] == ["Progress target = 1", "Number of users = 1"]


def test_change_owner():
    ctx = make_context({"SANDBOX/user99": ["KO1COBUILD_99"], "SANDBOX/user01": ["KO1COBUILD_01"], "SANDBOX/user02": []})
    params = {"user_num_from": 1, "user_num_to": 2, "key_select_method": "from_list",
              "project_key_select": "KO1COBUILD", "admin_TF": False}
    out = get_feature("change_owner").run(ctx, params, lambda p: None)
    assert out == "Successfully changed ownership for 2 project(s)"  # KO1COBUILD_02 does not exist
    assert ctx.client.projects["KO1COBUILD_99"].permissions["owner"] == "user99"
    assert ctx.client.projects["KO1COBUILD_01"].permissions["owner"] == "user01"

    params = dict(params, admin_TF=True)
    assert get_feature("change_owner").run(ctx, params, lambda p: None) == "Successfully changed ownership for 2 project(s)"
    assert ctx.client.projects["KO1COBUILD_01"].permissions["owner"] == "admin"


def test_sandbox_to_admin():
    ctx = make_context({"SANDBOX": ["A", "B"], "SANDBOX/user01": ["C"]})
    ctx.client.projects["A"].permissions["owner"] = "user01"
    ctx.client.fail.add("B")
    progress = []
    out = get_feature("sandbox_to_admin").run(ctx, {}, progress.append)
    assert out.startswith("Successfully changed owner of 1 project(s) to admin</br></br>&lt;A&gt;<br/>")
    assert "<h4>1 failure(s)</h4><ul><li>&lt;B&gt; — update failed</li></ul>" in out
    assert ctx.client.projects["A"].permissions["owner"] == "admin"
    assert ctx.client.projects["C"].permissions["owner"] == "admin"  # untouched: not directly in SANDBOX
    assert progress == [1]


# --- housekeeping -------------------------------------------------------------

DELETE_TREE = {
    "ROOT": ["ADMINV4"],
    "SANDBOX": ["SBX", "KEEP"],
    "SANDBOX/user99": ["KO1COBUILD_99"],
    "SANDBOX/user01": ["KO1COBUILD_01", "OWN_01"],
    "SANDBOX/user01/work": ["WORK_01"],
}


def test_delete_projects_user_num_mode_with_captured_log():
    lines = []
    ctx = make_context(DELETE_TREE)
    ctx.log = lines.append
    feature = get_feature("delete_projects")
    params = {"delete_type": "user_num", "delete_TF": True, "user_count": 1,
              "key_select_method": "from_list", "project_keys_list": ["KO1COBUILD"]}
    assert feature.progress_target(ctx, params) == 4
    out = feature.run(ctx, params, lambda p: None)
    assert out == (
        "<h4>Successfully deleted 2 project(s)</h4>"
        "<br/><b>user99</b> : &lt;KO1COBUILD_99&gt; <i>[+user99]</i>"
        "<br/><b>user01</b> : &lt;KO1COBUILD_01&gt; <i>[+user01]</i>"
        "<h4>Deleted 2 user folder(s)</h4>"
    )
    assert "Delete folder user99" in lines and "Delete folder user01" in lines
    assert ctx.client.deleted_projects() == ["KO1COBUILD_99", "KO1COBUILD_01"]


def test_delete_projects_dry_run_touches_nothing():
    ctx = make_context(DELETE_TREE)
    params = {"delete_type": "sandbox", "delete_TF": False, "projects_to_keep": ["KEEP"]}
    out = get_feature("delete_projects").run(ctx, params, lambda p: None)
    assert out == "<h4>Identified 1 project(s) to delete</h4>&lt;SBX&gt;<br/><h4>Identified 0 user folder(s)</h4>"
    assert ctx.client.calls == []


class FakeUserSettings:
    def __init__(self, store, login):
        self.store, self.login, self.enabled = store, login, store[login]

    def save(self):
        self.store[self.login] = self.enabled


class FakeUser:
    def __init__(self, store, login):
        self.store, self.login = store, login

    def get_settings(self):
        return FakeUserSettings(self.store, self.login)


def test_toggle_users_skips_instructor_and_others():
    store = {"user01": True, "user02": True, "user99": True, "admin": True, "userX": True}
    ctx = make_context()
    ctx.client.list_users = lambda: [{"login": login} for login in store]
    ctx.client.get_user = lambda login: FakeUser(store, login)
    out = get_feature("toggle_users").run(ctx, {"enable_or_disable": "disable"}, lambda p: None)
    assert out == "Successfully disabled 2 user(s)"
    assert store == {"user01": False, "user02": False, "user99": True, "admin": True, "userX": True}
    out = get_feature("toggle_users").run(ctx, {"enable_or_disable": "enable"}, lambda p: None)
    assert out == "Successfully enabled 2 user(s)"
    assert store["user01"] is True


class FakeExposedSettings:
    def __init__(self, raw):
        self.raw, self.saved = raw, False

    def get_raw(self):
        return self.raw

    def save(self):
        self.saved = True


def test_stop_sharing_keeps_prefixes():
    ctx = make_context({"ROOT": ["READONLY"]})
    raw = {"exposedObjects": {"objects": [{"localName": "credit_score", "rules": [
        {"targetProject": "KO4EVAL_01"}, {"targetProject": "DEMO_KO_CARDFRAUD"}, {"targetProject": "KO1COBUILD_01"},
    ]}]}}
    settings = FakeExposedSettings(raw)
    ctx.client.projects["READONLY"].get_settings = lambda: settings
    out = get_feature("stop_sharing").run(ctx, {"target_projects_to_keep": ["KO4EVAL", "DEMO_KO_CARDFRAUD"]}, lambda p: None)
    assert out == "Stopped sharing 1 shared project(s)"
    assert [r["targetProject"] for r in raw["exposedObjects"]["objects"][0]["rules"]] == ["KO4EVAL_01", "DEMO_KO_CARDFRAUD"]
    assert settings.saved

    ctx.client.projects["READONLY"].get_settings = lambda: FakeExposedSettings({"exposedObjects": {"objects": []}})
    with pytest.raises(RuntimeError, match="credit_score is not exposed"):
        get_feature("stop_sharing").run(ctx, {}, lambda p: None)


# --- infra (no AWS access: boto3 is a stub) -----------------------------------------

def test_api_node_status_without_boto3(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "boto3", None)  # make `import boto3` fail
    ctx = make_context()
    with pytest.raises(RuntimeError, match="boto3 is not installed"):
        get_feature("api_node_status").run(ctx, {}, lambda p: None)


def test_feature_record_is_frozen():
    feature = Feature(id="x", label="x", category="c", macro_folder="m", run=lambda c, p, cb: "")
    with pytest.raises(Exception):
        feature.id = "y"
