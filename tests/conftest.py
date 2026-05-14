"""Pytest fixtures for the Movie Star unit test suite.

A temp on-disk SQLite file (not :memory:) is used so the same data is
visible across every connection that Flask-SQLAlchemy opens during
request handling. The schema is dropped + recreated before each test
so tests cannot leak state into each other.

Fixtures exposed:

    app         — the Flask app configured for testing
    client      — a Flask test client
    make_user   — factory that inserts a User
    make_movie  — factory that inserts a Movie (and its Genres if given)
    login       — log the test client in as a given user via the session
"""
import os
import tempfile

# config.py raises if SECRET_KEY is missing, so plant one in the env
# BEFORE importing the app. The value is only ever used by pytest.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

import pytest  # noqa: E402  (import after env setup is intentional)
from sqlalchemy import create_engine  # noqa: E402

from app import app as _app, db as _db  # noqa: E402
from app.models import Genre, Movie, User  # noqa: E402,F401


# ── Session-scoped temp DB file ─────────────────────────────────────

@pytest.fixture(scope="session")
def temp_db_path():
    """One temp SQLite file shared by every test in the session."""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


# ── Core app + client fixtures ──────────────────────────────────────

@pytest.fixture
def app(temp_db_path):
    """Flask app with CSRF disabled and a freshly reset schema per test."""
    uri = f"sqlite:///{temp_db_path}"
    _app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=uri,
    )
    with _app.app_context():
        # Rebind the engine so Flask-SQLAlchemy actually talks to the
        # temp file rather than the engine cached from production config.
        try:
            _db.engine.dispose()
        except Exception:
            pass
        _db.engines[None] = create_engine(uri)
        _db.drop_all()
        _db.create_all()
        yield _app
        _db.session.remove()


@pytest.fixture
def client(app):
    """A Flask test client for HTTP-level assertions."""
    return app.test_client()


# ── Data factories ──────────────────────────────────────────────────

@pytest.fixture
def make_user(app):
    """Insert a User with sensible defaults; password is hashed."""
    def _make(username="alice", email=None, password="password123"):
        user = User(
            username=username,
            email=email or f"{username}@example.com",
        )
        user.set_password(password)
        _db.session.add(user)
        _db.session.commit()
        return user
    return _make


@pytest.fixture
def make_movie(app):
    """Insert a Movie; genres can be passed as a list of names."""
    def _make(title="Test Movie", release_year=2020, genres=None, **kwargs):
        defaults = {"director_name": "Test Director"}
        defaults.update(kwargs)
        movie = Movie(title=title, release_year=release_year, **defaults)
        if genres:
            attached = []
            for name in genres:
                g = _db.session.query(Genre).filter_by(name=name).first()
                if g is None:
                    g = Genre(name=name)
                    _db.session.add(g)
                attached.append(g)
            movie.genres = attached
        _db.session.add(movie)
        _db.session.commit()
        return movie
    return _make


# ── Auth helper ─────────────────────────────────────────────────────

@pytest.fixture
def login(client):
    """Log the test client in as the given user_id by writing the session.

    Faster than going through POST /login for tests that just need an
    authenticated request context (no need to exercise the auth flow).
    """
    def _login(user_id):
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user_id)
            sess["_fresh"] = True
    return _login
