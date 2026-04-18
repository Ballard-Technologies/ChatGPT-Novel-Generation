"""Shared pytest fixtures.

Environment variables must be set before the ``app`` module is imported,
since ``app.py`` builds the Flask application at import time.
"""
import os
import sys
import tempfile

# Ensure a predictable config before app.py is imported anywhere.
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
# Use a file-backed sqlite DB (not :memory:) so all SQLAlchemy connections
# and test-client threads share the same schema.
_TEST_DB_FD, _TEST_DB_PATH = tempfile.mkstemp(suffix='.sqlite', prefix='cngtest_')
os.close(_TEST_DB_FD)
os.environ.setdefault('DATABASE_URL', f'sqlite:///{_TEST_DB_PATH}')
os.environ.setdefault('RATELIMIT_STORAGE_URI', 'memory://')
os.environ.pop('ENV', None)  # stay in dev mode for tests

# Make the repository root importable.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402

import app as app_module  # noqa: E402
from models import db  # noqa: E402
from models.job import Job  # noqa: E402
from models.novel import Novel  # noqa: E402
from models.user import User  # noqa: E402


@pytest.fixture(scope='session')
def flask_app():
    flask_app = app_module.app
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SERVER_NAME='localhost.localdomain',
    )
    with flask_app.app_context():
        db.create_all()
    yield flask_app
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()
    try:
        os.unlink(_TEST_DB_PATH)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def _clean_db(flask_app):
    """Empty user/novel rows and reset rate-limit counters between tests."""
    with flask_app.app_context():
        # Novels and jobs reference users; delete them first so foreign-key
        # constraints are satisfied on engines that actually enforce them.
        db.session.query(Job).delete()
        db.session.query(Novel).delete()
        db.session.query(User).delete()
        db.session.commit()
    try:
        app_module.limiter.reset()
    except Exception:
        pass
    yield


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture
def csrf_client(flask_app):
    flask_app.config['WTF_CSRF_ENABLED'] = True
    try:
        yield flask_app.test_client()
    finally:
        flask_app.config['WTF_CSRF_ENABLED'] = False


def make_user(flask_app, username='testuser', password='password123'):
    with flask_app.app_context():
        user = User(username=User.normalize_username(username))
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def user_factory(flask_app):
    def _make(username='testuser', password='password123'):
        return make_user(flask_app, username=username, password=password)
    return _make


def login(client, username, password):
    return client.post(
        '/login',
        data={'username': username, 'password': password},
        follow_redirects=False,
    )
