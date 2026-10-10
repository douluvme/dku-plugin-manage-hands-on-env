"""Small HTML builders for the macros' ``resultType: HTML`` return values."""


def html_key(key):
    """Render a project key / folder name as ``&lt;KEY&gt;``."""
    return f"&lt;{key}&gt;"


def user_heading(user):
    """Start a per-user line: ``<br/><b>user07</b> :``."""
    return f"<br/><b>{user}</b> :"


def render_list(items, fmt=html_key):
    """``<ul><li>..</li>..</ul>`` of ``items`` (each passed through ``fmt``), or ``""``."""
    items = list(items)
    if not items:
        return ""
    return "<ul>" + "".join(f"<li>{fmt(item)}</li>" for item in items) + "</ul>"


def render_failures(failures):
    """``<h4>N failure(s)</h4><ul>..</ul>`` for ``(key, reason)`` pairs, or ``""``."""
    failures = list(failures)
    if not failures:
        return ""
    rows = "".join(f"<li>{html_key(key)} — {reason}</li>" for key, reason in failures)
    return f"<h4>{len(failures)} failure(s)</h4><ul>{rows}</ul>"


def render_result(title, items="", skipped=(), failures=()):
    """``<h4>title</h4>`` followed by the body, then optional skipped and failure sections.

    ``items`` is either a ready-made HTML fragment (str) or an iterable of keys that is
    rendered as a bulleted list.
    """
    body = items if isinstance(items, str) else render_list(items)
    msg = f"<h4>{title}</h4>{body}"

    skipped = list(skipped)
    if skipped:
        msg += f"<h4>{len(skipped)} skipped (already exist)</h4>{render_list(skipped)}"

    msg += render_failures(failures)
    return msg
