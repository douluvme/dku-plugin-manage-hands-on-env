"""Small helpers that build the HTML returned by the macros (resultType HTML)."""


def key_tag(key):
    """Render a project/folder key as ``&lt;KEY&gt;``."""
    return f"&lt;{key}&gt;"


def section(title, rows=()):
    """``<h4>title</h4>`` followed by a ``<ul>`` of ``rows`` when there are any."""
    html = f"<h4>{title}</h4>"
    rows = list(rows)
    if rows:
        html += "<ul>" + "".join(f"<li>{row}</li>" for row in rows) + "</ul>"
    return html


def render_result(title, body="", extra_sections=(), skipped=(), failures=()):
    """Assemble a macro result.

    ``title`` becomes the leading ``<h4>``, ``body`` is appended verbatim,
    ``extra_sections`` is an iterable of ``(title, rows)`` pairs, ``skipped``
    is a list of keys that already existed and ``failures`` a list of
    ``(key, reason)`` pairs.
    """
    html = section(title) + body
    for extra_title, rows in extra_sections:
        html += section(extra_title, rows)
    skipped = list(skipped)
    if skipped:
        html += section(f"{len(skipped)} skipped (already exist)", (key_tag(k) for k in skipped))
    failures = list(failures)
    if failures:
        html += section(f"{len(failures)} failure(s)",
                        (f"{key_tag(k)} — {reason}" for k, reason in failures))
    return html
