"""Form schemas derived from the macro descriptors."""
import pytest

from managehandsonenv.features import FEATURES, get_feature
from managehandsonenv.starters import STARTERS
from managehandsonenv.webapp.forms import coerce_params, form_schema, param_schema


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
