"""Small HTML builders for macro results (``resultType: HTML``)."""
import html
from typing import Dict, Iterable, List, Tuple


def html_key(key: str) -> str:
    """Render a project key / folder name as ``&lt;KEY&gt;``."""
    return "&lt;{}&gt;".format(html.escape(str(key)))


def heading(text: str) -> str:
    return "<h4>{}</h4>".format(text)


def bullet_list(items: Iterable[str]) -> str:
    """``<ul>`` of already-rendered HTML items."""
    return "<ul>{}</ul>".format("".join("<li>{}</li>".format(item) for item in items))


def key_lines(keys: Iterable[str]) -> str:
    """One ``&lt;KEY&gt;<br/>`` line per key."""
    return "".join("{}<br/>".format(html_key(key)) for key in keys)


def grouped_lines(groups: Dict[str, List[str]]) -> str:
    """``<br/><b>group</b> : item item ...`` for every group, in insertion order."""
    return "".join(
        "<br/><b>{}</b> : {}".format(html.escape(str(name)), " ".join(items))
        for name, items in groups.items()
    )


def failures_section(failures: Iterable[Tuple[str, str]]) -> str:
    """``<h4>N failure(s)</h4>`` plus a list of ``&lt;KEY&gt; — reason``; empty when there are none."""
    failures = list(failures)
    if not failures:
        return ""
    rows = ("{} — {}".format(html_key(key), html.escape(str(reason))) for key, reason in failures)
    return heading("{} failure(s)".format(len(failures))) + bullet_list(rows)


def render_result(
    title: str,
    body: str = "",
    skipped: Iterable[str] = (),
    failures: Iterable[Tuple[str, str]] = (),
    skipped_label: str = "skipped (already exist)",
) -> str:
    """``<h4>title</h4>`` + body, then optional skipped and failure sections."""
    out = heading(title) + body
    skipped = list(skipped)
    if skipped:
        out += heading("{} {}".format(len(skipped), skipped_label)) + bullet_list(html_key(k) for k in skipped)
    out += failures_section(failures)
    return out
