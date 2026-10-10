"""Shared library of the manage-hands-on-env plugin.

Modules:
- ``settings``: ``Settings`` (plugin-level values with historical defaults)
- ``context``: ``Context`` handed to every feature (client, settings, project key, log)
- ``features``: the registry of everything the plugin can do; macros and the webapp call it
- ``base``: ``HandsOnRunnable`` (admin guard, API client) delegating to a feature by id
- ``users``: user numbering and per-user folders under the sandbox folder
- ``projects``: duplicate / change owner / delete / existence check
- ``deletion``: delete plans and their execution (dry-run or real)
- ``starters``: the standard starter-project list
- ``aws``: boto3 helpers
- ``results``: HTML result builders
- ``descriptors``: comment-tolerant parsing of the plugin's JSON descriptors
- ``webapp``: form schemas, background jobs and the Flask API of the console webapp
"""
