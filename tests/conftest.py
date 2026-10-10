"""Test bootstrap: stub the DSS-only modules and put python-lib on the path.

``dataiku`` (with ``dataiku.runnables.Runnable``) and ``boto3`` do not exist
outside a DSS code environment, so minimal stand-ins are injected into
``sys.modules`` before anything imports the library.
"""
import importlib.util
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "python-lib"
RUNNABLES_DIR = ROOT / "python-runnables"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # so tests can `import fakes`


def _install_stubs():
    if "dataiku" not in sys.modules:
        dataiku = types.ModuleType("dataiku")
        runnables = types.ModuleType("dataiku.runnables")

        class Runnable(object):
            """Trivial stand-in for dataiku.runnables.Runnable."""

            def __init__(self, project_key, config, plugin_config):
                pass

            def get_progress_target(self):
                return None

            def run(self, progress_callback):
                raise NotImplementedError

        runnables.Runnable = Runnable
        dataiku.runnables = runnables

        def api_client():
            raise RuntimeError("dataiku.api_client() stub: patch it with a FakeClient in the test")

        dataiku.api_client = api_client
        sys.modules["dataiku"] = dataiku
        sys.modules["dataiku.runnables"] = runnables

    if "boto3" not in sys.modules:
        boto3 = types.ModuleType("boto3")

        def client(*args, **kwargs):
            raise RuntimeError("boto3 stub: no AWS access in tests")

        boto3.client = client
        sys.modules["boto3"] = boto3


_install_stubs()


def runnable_dirs():
    """Every macro folder under python-runnables, sorted."""
    return sorted(p for p in RUNNABLES_DIR.iterdir() if p.is_dir() and (p / "runnable.py").exists())


def load_runnable(folder):
    """Import ``<folder>/runnable.py`` as a standalone module."""
    folder = pathlib.Path(folder)
    name = "runnable_" + "".join(c if c.isalnum() else "_" for c in folder.name)
    spec = importlib.util.spec_from_file_location(name, folder / "runnable.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_client(monkeypatch):
    """A FakeClient that ``dataiku.api_client()`` also returns."""
    from fakes import FakeClient

    client = FakeClient()
    monkeypatch.setattr(sys.modules["dataiku"], "api_client", lambda: client)
    return client
