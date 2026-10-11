"""boto3 client construction: credentials come from the preset, never from the instance role."""
import sys
import types

import pytest

from managehandsonenv.aws import NO_CREDENTIALS_MESSAGE, boto_client
from managehandsonenv.features import get_feature
from test_features import make_context


@pytest.fixture
def fake_boto3(monkeypatch):
    calls = []
    module = types.ModuleType("boto3")
    module.client = lambda service, **kwargs: calls.append((service, kwargs)) or "client"
    monkeypatch.setitem(sys.modules, "boto3", module)
    return calls


def test_boto_client_uses_the_preset_keys(fake_boto3):
    assert boto_client("rds", {"aws_access_key_id": "k", "aws_secret_access_key": "s"}, "ap-northeast-2") == "client"
    assert fake_boto3 == [("rds", {"region_name": "ap-northeast-2", "aws_access_key_id": "k", "aws_secret_access_key": "s"})]


@pytest.mark.parametrize("preset", [{}, None, {"aws_access_key_id": "k"}, {"mode": "PRESET", "name": "x"}])
def test_boto_client_refuses_to_run_without_a_key_pair(fake_boto3, preset):
    with pytest.raises(RuntimeError) as err:
        boto_client("rds", preset, "ap-northeast-2")
    assert str(err.value) == NO_CREDENTIALS_MESSAGE
    assert fake_boto3 == []


def test_infra_feature_logs_the_credential_source_then_fails_clearly(fake_boto3):
    log = []
    ctx = make_context()
    ctx.log = log.append
    with pytest.raises(RuntimeError, match="No AWS credentials"):
        get_feature("db_status").run(ctx, {}, lambda n: None)
    assert log == ["AWS credentials: not configured"]
