"""The Flask API of the console webapp, through Flask's test client."""
import threading

import pytest
from fakes import FakeClient

from managehandsonenv.context import Context
from managehandsonenv.features import FEATURES
from managehandsonenv.features.types import Feature
from managehandsonenv.webapp.api import register_routes
from managehandsonenv.webapp.jobs import JobManager

flask = pytest.importorskip("flask")


def build_app(project_key="ADMINV4", tree=None, component_config=None):
    client = FakeClient().build(tree or {})
    factory = lambda: Context(client=client, project_key=project_key, component_config=component_config or {},  # noqa: E731
                              component_label="webapp settings")
    app = flask.Flask("hands-on-test")
    manager = JobManager(factory)
    register_routes(app, manager, factory)
    return app.test_client(), manager, client


def test_context_lists_features_by_category():
    http, _, _ = build_app()
    body = http.get("/api/context").get_json()
    assert body["project_key"] == "ADMINV4" and body["admin_project_key"] == "ADMINV4"
    assert body["allowed"] is True
    assert body["settings"]["sandbox_folder"] == "SANDBOX"
    assert body["aws"] == {"configured": False, "source": None}
    assert [c["name"] for c in body["categories"]][0] == "⚠️ Hands-on 1: Manage Starter Projects"
    assert [c["menu_name"] for c in body["categories"]] == ["Starter Projects", "Housekeeping", "Workshop Environment"]
    ids = [f["id"] for c in body["categories"] for f in c["features"]]
    assert ids == list(FEATURES)
    first = body["categories"][0]["features"][0]
    assert first["menu_label"] == "Duplicate Starters"
    assert first["label"] == "Duplicate Starter Projects" and first["macro_label"] == "1.Duplicate Starter Projects"
    assert body["categories"][0]["display_name"] == "Manage Starter Projects"
    delete = next(f for c in body["categories"] for f in c["features"] if f["id"] == "delete_projects")
    assert delete["destructive"] and delete["confirm"]


def test_context_and_form_report_the_aws_credential_source():
    http, _, _ = build_app(component_config={"aws_account": {"aws_access_key_id": "k", "aws_secret_access_key": "s"}})
    assert http.get("/api/context").get_json()["aws"] == {"configured": True, "source": "webapp settings"}
    chips = http.get("/api/features/db_status/form").get_json()["settings"]
    assert chips[-1] == {"key": "aws_account", "label": "AWS account", "value": "webapp settings"}


def test_form_and_unknown_feature():
    http, _, _ = build_app()
    body = http.get("/api/features/duplicate_starters/form").get_json()
    assert body["feature_id"] == "duplicate_starters"
    assert body["label"] == "Duplicate Starter Projects"
    assert [p["name"] for p in body["params"]] == ["user_count", "key_select_method", "project_keys_list", "project_keys_input"]
    assert body["settings"] == [{"key": "admin_project_key", "label": "Admin project", "value": "ADMINV4"},
                                {"key": "sandbox_folder", "label": "Sandbox folder", "value": "SANDBOX"}]
    assert http.get("/api/features/nope/form").status_code == 404
    assert len(http.get("/api/features").get_json()["features"]) == len(FEATURES)


def test_run_job_end_to_end():
    http, manager, client = build_app(tree={"ROOT": ["KO1COBUILD"], "SANDBOX": []})
    response = http.post("/api/jobs", json={
        "feature_id": "duplicate_starters",
        "params": {"user_count": "1", "key_select_method": "from_list", "project_keys_list": ["KO1COBUILD"]},
    })
    assert response.status_code == 202, response.get_json()
    job = response.get_json()["job"]
    manager.wait(manager.get(job["id"]), timeout=5)

    body = http.get("/api/jobs/{}".format(job["id"])).get_json()["job"]
    assert body["status"] == "succeeded"
    assert body["progress"] == body["progress_target"] == 2
    assert body["result_html"].startswith("<h4>Successfully duplicated 2 project(s)</h4>")
    assert "Number of users = 2" in body["log"]
    assert client.get_project_folder("user01").list_project_keys() == ["KO1COBUILD_01"]

    tail = http.get("/api/jobs/{}?log_from={}".format(job["id"], body["log_length"] - 1)).get_json()["job"]
    assert len(tail["log"]) == 1

    history = http.get("/api/jobs").get_json()
    assert history["current"] is None
    assert [j["id"] for j in history["jobs"]] == [job["id"]]
    assert history["jobs"][0]["log"] == []  # history entries omit the log


def test_refused_outside_admin_project_and_bad_requests():
    http, _, _ = build_app(project_key="OTHER")
    assert http.get("/api/context").get_json()["allowed"] is False
    response = http.post("/api/jobs", json={"feature_id": "db_status", "params": {}})
    assert response.status_code == 403
    assert "ADMINV4" in response.get_json()["error"]

    http, _, _ = build_app()
    assert http.post("/api/jobs", json={"feature_id": "nope"}).status_code == 400
    assert http.post("/api/jobs", json={"feature_id": "duplicate_starters",
                                        "params": {"user_count": "many"}}).status_code == 400
    assert http.get("/api/jobs/zzz").status_code == 404


def test_second_job_is_rejected_while_one_runs(monkeypatch):
    gate = threading.Event()

    def slow(ctx, params, progress):
        gate.wait(5)
        return "ok"

    slow_feature = Feature(id="db_status", label="slow", category="c", macro_folder="3-2-get-db-class", run=slow)
    monkeypatch.setitem(FEATURES, "db_status", slow_feature)

    http, manager, _ = build_app()
    first = http.post("/api/jobs", json={"feature_id": "db_status", "params": {}})
    assert first.status_code == 202
    second = http.post("/api/jobs", json={"feature_id": "db_status", "params": {}})
    assert second.status_code == 409
    assert second.get_json()["job"]["id"] == first.get_json()["job"]["id"]
    assert http.get("/api/jobs").get_json()["current"]["id"] == first.get_json()["job"]["id"]
    gate.set()
    manager.wait(manager.get(first.get_json()["job"]["id"]), timeout=5)
