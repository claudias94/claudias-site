"""Production entry point.

Run with a real WSGI server, e.g.:
    gunicorn wsgi:app --bind 0.0.0.0:${PORT:-8000} --workers 3

Do not use this with `flask run` or `python run.py` — those already load
the app themselves via run.py. This file exists only for WSGI servers that
expect to import an `app` object.
"""
from app import create_app

app = create_app()
