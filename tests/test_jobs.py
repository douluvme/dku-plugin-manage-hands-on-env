"""Background jobs: progress, captured log, failures, one at a time, history."""
import sys
import threading
import time

import pytest
from fakes import FakeClient

from managehandsonenv.context import Context
from managehandsonenv.features.types import Feature
from managehandsonenv.webapp.jobs import FAILED, SUCCEEDED, JobManager, JobRunning


def make_feature(run, target=None, **kwargs):
    return Feature(id=kwargs.pop("id", "f"), label=kwargs.pop("label", "Fake"), category="c", macro_folder="m",
                   run=run, progress_target=target, **kwargs)


@pytest.fixture
def manager():
    context_factory = lambda: Context(client=FakeClient(), project_key="ADMINV4")  # noqa: E731
    return JobManager(context_factory, history_size=3)


def test_job_captures_progress_log_and_result(manager):
    def run(ctx, params, progress):
        ctx.log("hello {}".format(params["x"]))
        print("printed too")
        progress(1)
        progress(2)
        return "<b>done</b>"

    job = manager.start(make_feature(run, target=lambda ctx, params: 2), {"x": 1})
    manager.wait(job, timeout=5)

    assert job.status == SUCCEEDED
    assert job.progress == 2 and job.progress_target == 2
    assert job.log == ["hello 1", "printed too"]
    assert job.result_html == "<b>done</b>"
    assert job.error is None
    assert job.started_at and job.finished_at and not job.active
    assert job.to_dict(log_from=1)["log"] == ["printed too"]
    assert job.to_dict()["log_length"] == 2


def test_failed_job_keeps_traceback_and_partial_log(manager):
    def run(ctx, params, progress):
        print("before", end="")
        raise ValueError("boom")

    job = manager.start(make_feature(run), {})
    manager.wait(job, timeout=5)
    assert job.status == FAILED
    assert "ValueError: boom" in job.error
    assert job.log == ["before"]
    assert job.result_html is None


def test_only_one_job_at_a_time(manager):
    gate = threading.Event()

    def run(ctx, params, progress):
        gate.wait(5)
        return "ok"

    first = manager.start(make_feature(run, label="slow"), {})
    with pytest.raises(JobRunning) as info:
        manager.start(make_feature(lambda c, p, cb: "x"), {})
    assert info.value.job is first
    assert manager.current() is first
    gate.set()
    manager.wait(first, timeout=5)
    assert manager.current() is None
    second = manager.start(make_feature(lambda c, p, cb: "x"), {})
    manager.wait(second, timeout=5)
    assert second.status == SUCCEEDED


def test_history_is_most_recent_first_and_bounded(manager):
    jobs = []
    for i in range(5):
        job = manager.start(make_feature(lambda c, p, cb: "x", id="f{}".format(i)), {"i": i})
        manager.wait(job, timeout=5)
        jobs.append(job)
    history = manager.history()
    assert len(history) == 3
    assert [j.id for j in history] == [j.id for j in reversed(jobs[-3:])]
    assert manager.get(jobs[0].id) is None
    assert manager.get(jobs[-1].id) is jobs[-1]


def test_stdout_router_leaves_other_threads_alone(manager, capsys):
    gate = threading.Event()

    def run(ctx, params, progress):
        print("from job")
        gate.wait(5)
        return "x"

    job = manager.start(make_feature(run), {})
    deadline = time.time() + 5
    while "from job" not in job.log and time.time() < deadline:
        time.sleep(0.01)
    assert "from job" in job.log, "job output was not routed to the job"
    print("from test thread")
    gate.set()
    manager.wait(job, timeout=5)
    assert job.log == ["from job"]
    out = capsys.readouterr().out
    assert "from job" in out and "from test thread" in out  # everything still reaches real stdout
    assert type(sys.stdout).__name__ == "_StdoutRouter"
