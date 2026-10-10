"""Shared library of the manage-hands-on-env plugin.

Modules:
- ``base``: ``HandsOnRunnable`` (admin guard, API client) and ``Settings`` (plugin-level values)
- ``users``: user numbering and per-user folders under the sandbox folder
- ``projects``: duplicate / change owner / delete / existence check
- ``starters``: the standard starter-project list
- ``aws``: boto3 helpers
- ``results``: HTML result builders
"""
