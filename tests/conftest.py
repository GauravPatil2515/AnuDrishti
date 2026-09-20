import sys
from pathlib import Path

# Ensure root and backend are on sys.path for direct test runs and IDE language servers
_root = Path(__file__).resolve().parent.parent
_backend = _root / "backend"
for p in [str(_root), str(_backend)]:
    if p not in sys.path:
        sys.path.insert(0, p)

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
