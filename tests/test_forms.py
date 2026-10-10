"""Form schemas derived from the macro descriptors."""
import pytest
from conftest import ROOT

from managehandsonenv.descriptors import macro_descriptor
from managehandsonenv.features import FEATURES, get_feature
from managehandsonenv.features.descriptor_data import MACRO_DESCRIPTORS
from managehandsonenv.starters import STARTERS
from managehandsonenv.webapp.forms import coerce_params, form_schema, param_schema


def test_descriptor_snapshot_matches_the_files():
    """The webapp reads a generated snapshot (DSS copies python-lib only); it must not drift."""
    folders = sorted(p.name for p in (ROOT / "python-runnables").iterdir() if (p / "runnable.json").exists())
    assert sorted(MACRO_DESCRIPTORS) == folders
    for folder in folders:
        data = macro_descriptor(folder)
        assert MACRO_DESCRIPTORS[folder] == {"meta": data["meta"], "params": data["params"]}, (
            "{}: snapshot is stale, run `make sync`".format(folder))


def test_form_schema_does_not_touch_the_filesystem(monkeypatch):
    import managehandsonenv.descriptors as descriptors

    monkeypatch.setattr(descriptors, "plugin_root", lambda: ROOT / "does-not-exist")
    for feature in FEATURES.values():
        assert form_schema(feature)["params"] is not None


@pytest.mark.parametrize("feature_id", list(FEATURES))
def test_every_feature_has_a_renderable_form(feature_id):
    schema = form_schema(get_feature(feature_id))
    assert schema["feature_id"] == feature_id
    assert schema["label"] and schema["category"]
    for param in schema["params"]:
        assert param["name"]
        assert param["type"] in {"INT", "DOUBLE", "STRING", "PASSWORD", "TEXTAREA", "BOOLEAN", "SELECT", "MULTISELECT", "STRINGS"}
        assert "unsupportedType" not in param, param
        if param["type"] in ("SELECT", "MULTISELECT"):
            assert param["choices"], param["name"]


def test_preset_params_are_hidden_and_starters_injected():
    db = form_schema(get_feature("modify_db_class"))
    assert [p["name"] for p in db["params"]] == ["db_class", "wait_TF"]  # aws_account (PRESET) hidden
    assert db["destructive"] and db["confirm"]

    dup = form_schema(get_feature("duplicate_starters"))
    starters = next(p for p in dup["params"] if p["name"] == "project_keys_list")
    assert starters["type"] == "MULTISELECT"
    assert starters["choices"] == STARTERS
    assert starters["visibilityCondition"] == "model.key_select_method == 'from_list'"
    assert not dup["destructive"]


def test_form_schema_carries_settings_and_label_overrides():
    from managehandsonenv.settings import Settings

    schema = form_schema(get_feature("delete_projects"), settings=Settings(sandbox_folder="SBX"))
    assert schema["label"] == "Delete Starter Projects" and schema["macro_label"] == "1.Delete Starter Projects"
    assert schema["category"] == "Housekeeping"
    assert next(p for p in schema["params"] if p["name"] == "delete_TF")["label"] == "Perform deletion"
    assert schema["settings"] == [{"key": "admin_project_key", "label": "Admin project", "value": "ADMINV4"},
                                  {"key": "sandbox_folder", "label": "Sandbox folder", "value": "SBX"}]
    assert form_schema(get_feature("delete_projects"))["settings"] == []  # no settings given


def test_param_schema_falls_back_to_string_for_unknown_types():
    schema = param_schema({"name": "ds", "type": "DATASET", "label": "Dataset"})
    assert schema["type"] == "STRING" and schema["unsupportedType"] == "DATASET"


def test_coerce_params_applies_defaults_and_types():
    schema = form_schema(get_feature("delete_projects"))
    params = coerce_params(schema, {"user_count": "2", "delete_TF": "true", "project_keys_input": "A\n\nB ",
                                    "projects_to_keep": ["K", ""]})
    assert params["user_count"] == 2
    assert params["delete_TF"] is True
    assert params["delete_type"] == "user_num"          # default from the descriptor
    assert params["key_select_method"] == "from_list"
    assert params["project_keys_input"] == ["A", "B"]
    assert params["projects_to_keep"] == ["K"]
    assert params["project_keys_list"] == []            # mandatory MULTISELECT without a default

    assert coerce_params(schema, {})["delete_TF"] is False
    with pytest.raises(ValueError):
        coerce_params(schema, {"user_count": "many"})
