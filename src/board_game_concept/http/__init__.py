"""The HTTP tier the CLI can talk to.

Reads today; writes and long-poll are their own later steps. The Flask app
lives in `app.py`; the view builders it computes with live in `views.py`,
shared with the `cli/` package through a re-export shim.
"""
