from collections import OrderedDict

from managehandsonenv.results import (
    bullet_list,
    failures_section,
    folder_marker,
    grouped_lines,
    heading,
    html_key,
    key_lines,
    render_result,
)


def test_html_key_escapes():
    assert html_key("KO1COBUILD_01") == "&lt;KO1COBUILD_01&gt;"
    assert html_key("a<b") == "&lt;a&lt;b&gt;"


def test_folder_marker_and_heading():
    assert folder_marker("user01") == "<i>[+user01]</i>"
    assert heading("x") == "<h4>x</h4>"


def test_lists():
    assert bullet_list(["a", "b"]) == "<ul><li>a</li><li>b</li></ul>"
    assert key_lines(["A", "B"]) == "&lt;A&gt;<br/>&lt;B&gt;<br/>"
    assert grouped_lines(OrderedDict([("user99", ["x", "y"]), ("user01", [])])) == "<br/><b>user99</b> : x y<br/><b>user01</b> : "


def test_failures_section():
    assert failures_section([]) == ""
    assert failures_section([("K", "boom & bust")]) == "<h4>1 failure(s)</h4><ul><li>&lt;K&gt; — boom &amp; bust</li></ul>"


def test_render_result():
    out = render_result("Successfully duplicated 1 project(s)", "<br/>body", skipped=["S"], failures=[("F", "why")])
    assert out == (
        "<h4>Successfully duplicated 1 project(s)</h4><br/>body"
        "<h4>1 skipped (already exist)</h4><ul><li>&lt;S&gt;</li></ul>"
        "<h4>1 failure(s)</h4><ul><li>&lt;F&gt; — why</li></ul>"
    )
    assert render_result("t") == "<h4>t</h4>"
