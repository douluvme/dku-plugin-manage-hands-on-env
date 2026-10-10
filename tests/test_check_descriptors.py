import importlib.util
import pathlib

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_descriptors.py"
spec = importlib.util.spec_from_file_location("check_descriptors", SCRIPT)
check_descriptors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_descriptors)


def test_strip_comments_keeps_strings_intact():
    text = '{"url": "https://x/y", "a": "/* not a comment */", // trailing\n/* block\n */ "b": 1}'
    assert check_descriptors.strip_comments(text) == '{"url": "https://x/y", "a": "/* not a comment */", \n "b": 1}'


def test_strip_comments_rejects_hash_comments():
    with pytest.raises(check_descriptors.DescriptorError, match="line 2"):
        check_descriptors.strip_comments('{\n# nope\n"a": "#ok"}')
    assert check_descriptors.strip_comments('{"a": "#ok"}') == '{"a": "#ok"}'


def test_parse_descriptor_detects_duplicate_keys(tmp_path):
    path = tmp_path / "runnable.json"
    path.write_text('{"params": [], "params": []}', encoding="utf-8")
    with pytest.raises(check_descriptors.DescriptorError, match="duplicate key 'params'"):
        check_descriptors.parse_descriptor(path)


def test_parse_descriptor_tolerates_trailing_comma(tmp_path):
    path = tmp_path / "runnable.json"
    path.write_text('{"params": [ {"name": "a"}, ], }', encoding="utf-8")
    assert check_descriptors.parse_descriptor(path) == {"params": [{"name": "a"}]}


def test_repository_descriptors_pass():
    assert check_descriptors.main() == 0
