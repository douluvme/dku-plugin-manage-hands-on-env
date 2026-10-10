"""Backend pieces of the "Hands-on Workshop Console" plugin webapp.

- :mod:`forms`: the form schema of a feature, derived from its macro descriptor
- :mod:`jobs`: background execution of a feature with progress, log and history
- :mod:`api`: the Flask routes, registered on the ``app`` DSS provides

Nothing here imports ``dataiku``; ``webapps/hands-on-console/backend.py`` wires
the pieces to the DSS runtime.
"""
