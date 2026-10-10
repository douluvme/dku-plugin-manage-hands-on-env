"""Background execution of a feature, with progress, captured log and history.

Only one job runs at a time: the features are destructive and must not
overlap. Everything a job (or the library code it calls) prints while running
is captured into the job's log: the manager replaces ``sys.stdout`` with a
router that sends each thread's output to the job bound to that thread, and
still to the real stdout (the DSS backend log).
"""
import sys
import threading
import time
import traceback
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from managehandsonenv.context import Context
from managehandsonenv.features.types import Feature

QUEUED = "queued"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
ACTIVE = (QUEUED, RUNNING)


class JobRunning(RuntimeError):
    """Raised by :meth:`JobManager.start` while another job is active."""

    def __init__(self, job: "Job"):
        super().__init__("Job {} ({}) is still {}".format(job.id, job.label, job.status))
        self.job = job


@dataclass
class Job:
    id: str
    feature_id: str
    label: str
    params: Dict[str, Any]
    destructive: bool = False
    status: str = QUEUED
    progress: int = 0
    progress_target: Optional[int] = None
    log: List[str] = field(default_factory=list)
    result_html: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    _partial: str = field(default="", repr=False)

    def set_progress(self, value: int) -> None:
        self.progress = int(value)

    def write(self, text: str) -> None:
        """Receive raw stdout fragments and keep whole lines."""
        if not text:
            return
        self._partial += text
        while "\n" in self._partial:
            line, self._partial = self._partial.split("\n", 1)
            self.log.append(line)

    def flush_partial(self) -> None:
        if self._partial:
            self.log.append(self._partial)
            self._partial = ""

    @property
    def active(self) -> bool:
        return self.status in ACTIVE

    def to_dict(self, log_from: int = 0) -> Dict[str, Any]:
        return {
            "id": self.id,
            "feature_id": self.feature_id,
            "label": self.label,
            "params": self.params,
            "destructive": self.destructive,
            "status": self.status,
            "active": self.active,
            "progress": self.progress,
            "progress_target": self.progress_target,
            "log": self.log[log_from:],
            "log_length": len(self.log),
            "result_html": self.result_html,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class _StdoutRouter:
    """A ``sys.stdout`` replacement that also copies a thread's output to its bound job."""

    def __init__(self, original):
        self._original = original
        self._local = threading.local()

    def bind(self, job: Optional[Job]) -> None:
        self._local.job = job

    def write(self, text):
        job = getattr(self._local, "job", None)
        if job is not None:
            job.write(text)
        return self._original.write(text)

    def flush(self):
        return self._original.flush()

    def __getattr__(self, name):
        return getattr(self._original, name)


class JobManager:
    """Runs one feature at a time in a background thread and keeps the recent jobs."""

    def __init__(self, context_factory: Callable[[], Context], history_size: int = 50):
        self._context_factory = context_factory
        self._history_size = history_size
        self._lock = threading.Lock()
        self._jobs: "OrderedDict[str, Job]" = OrderedDict()
        self._threads: Dict[str, threading.Thread] = {}

    @staticmethod
    def _router() -> _StdoutRouter:
        """The router currently wrapping ``sys.stdout`` (installed on first use).

        Looked up when a job starts rather than once at construction, so that a
        ``sys.stdout`` swapped in the meantime (pytest's capture, a DSS log
        redirection) is the one being wrapped.
        """
        if not isinstance(sys.stdout, _StdoutRouter):
            sys.stdout = _StdoutRouter(sys.stdout)
        return sys.stdout

    # --- public API ----------------------------------------------------------
    def current(self) -> Optional[Job]:
        for job in reversed(self._jobs.values()):
            if job.active:
                return job
        return None

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def history(self, limit: int = 20) -> List[Job]:
        """Most recent first."""
        return list(reversed(self._jobs.values()))[:limit]

    def start(self, feature: Feature, params: Dict[str, Any]) -> Job:
        with self._lock:
            running = self.current()
            if running is not None:
                raise JobRunning(running)
            job = Job(
                id=uuid.uuid4().hex[:8],
                feature_id=feature.id,
                label=feature.label,
                params=dict(params),
                destructive=feature.needs_confirmation(params),
            )
            self._jobs[job.id] = job
            while len(self._jobs) > self._history_size:
                oldest = next(iter(self._jobs))
                if self._jobs[oldest].active:
                    break
                del self._jobs[oldest]
                self._threads.pop(oldest, None)
            thread = threading.Thread(target=self._run, args=(job, feature), name="hands-on-job-" + job.id, daemon=True)
            self._threads[job.id] = thread
            thread.start()
        return job

    def wait(self, job: Job, timeout: Optional[float] = None) -> Job:
        """Block until the job finishes (tests and synchronous callers)."""
        thread = self._threads.get(job.id)
        if thread is not None:
            thread.join(timeout)
        return job

    # --- worker --------------------------------------------------------------
    def _run(self, job: Job, feature: Feature) -> None:
        router = self._router()
        router.bind(job)
        job.started_at = time.time()
        job.status = RUNNING
        try:
            ctx = self._context_factory()
            if feature.progress_target is not None:
                job.progress_target = feature.progress_target(ctx, job.params)
            job.result_html = feature.run(ctx, job.params, job.set_progress)
            if job.progress_target is not None:
                job.progress = job.progress_target
            job.status = SUCCEEDED
        except Exception:
            job.error = traceback.format_exc()
            job.status = FAILED
        finally:
            job.flush_partial()
            job.finished_at = time.time()
            router.bind(None)
