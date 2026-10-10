import pytest
from fakes import FakeClient

from managehandsonenv.projects import (
    delete_project,
    duplicate_project,
    existing_project_keys,
    project_exists,
    set_project_owner,
    suffixed_key,
)


def test_suffixed_key():
    assert suffixed_key("KO1COBUILD", "01") == "KO1COBUILD_01"


def test_project_exists_uses_listing():
    client = FakeClient().build({"ROOT": ["A"]})
    assert project_exists(client, "A")
    assert not project_exists(client, "B")
    assert existing_project_keys(client) == {"A"}


def test_set_project_owner_success():
    client = FakeClient().build({"ROOT": ["KO1COBUILD_01"]})
    assert set_project_owner(client, "KO1COBUILD_01", "user01") is True
    assert client.projects["KO1COBUILD_01"].permissions["owner"] == "user01"
    assert ("set_permissions", "KO1COBUILD_01", "user01") in client.calls


def test_set_project_owner_returns_false_and_logs_on_api_error(capsys):
    client = FakeClient().build({"ROOT": ["KO1COBUILD_01"]})
    client.fail.add("KO1COBUILD_01")
    assert set_project_owner(client, "KO1COBUILD_01", "user01") is False
    assert client.projects["KO1COBUILD_01"].permissions["owner"] == "admin"
    captured = capsys.readouterr()
    assert "Failed to set owner of KO1COBUILD_01" in captured.out
    assert "API error on project KO1COBUILD_01" in captured.out


def test_set_project_owner_missing_project_returns_false(capsys):
    client = FakeClient()
    assert set_project_owner(client, "NOPE_01", "user01") is False
    assert "Failed to set owner of NOPE_01" in capsys.readouterr().out


def test_duplicate_project_default_tags():
    client = FakeClient().build({"ROOT": ["KO1COBUILD"], "SANDBOX/user01": []})
    client.projects["KO1COBUILD"].metadata["label"] = "Start 1 Cobuild"
    folder = client.get_project_folder("user01")

    assert duplicate_project(client, "KO1COBUILD", "KO1COBUILD_01", folder) == "KO1COBUILD_01"

    new_project = client.projects["KO1COBUILD_01"]
    assert new_project.folder is folder
    assert "KO1COBUILD_01" in folder.list_project_keys()
    assert new_project.metadata["label"] == "Start 1 Cobuild"
    assert new_project.metadata["tags"] == ["duplicated", "Start 1 Cobuild"]
    assert ("duplicate", "KO1COBUILD", "KO1COBUILD_01") in client.calls


def test_duplicate_project_custom_tags_and_error():
    client = FakeClient().build({"ROOT": ["SRC", "TAKEN"]})
    duplicate_project(client, "SRC", "SRC_99", client.root, tags=["x"])
    assert client.projects["SRC_99"].metadata["tags"] == ["x"]
    with pytest.raises(RuntimeError):
        duplicate_project(client, "SRC", "TAKEN", client.root)


def test_delete_project_removes_and_raises_on_error():
    client = FakeClient().build({"SANDBOX/user01": ["A", "B"]})
    delete_project(client, "A")
    assert "A" not in client.projects
    assert client.get_project_folder("user01").list_project_keys() == ["B"]

    client.fail.add("B")
    with pytest.raises(RuntimeError):
        delete_project(client, "B")
    assert "B" in client.projects
