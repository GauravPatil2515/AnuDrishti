"""
Shared pytest fixtures for AnuDrishti tests.
"""
import pytest
from flask import Flask
import routes.pharmaguard as pg


@pytest.fixture
def app():
    """Flask test application with pharmaguard blueprint registered."""
    app = Flask(__name__)
    app.register_blueprint(pg.pharmaguard_bp)
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
