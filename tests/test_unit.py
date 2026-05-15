"""Unit tests for the Movie Star Flask app.

Each module is exercised on at least one happy path and one error path
where applicable. Tests use a temp SQLite database and never touch the
network.

Run with:

    python -m unittest tests.test_unit -v

or:

    python -m unittest discover tests -v
"""
import os
import tempfile
import unittest
from pathlib import Path

# config.py raises if SECRET_KEY is missing, so plant one in the env
# BEFORE importing the app. The value is only ever used by unittest.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unittest-only")

from sqlalchemy import create_engine  # noqa: E402

from app import app, db  # noqa: E402
from app.models import Genre, Movie, Review, ReviewLike, User, WatchlistItem  # noqa: E402


class MovieStarUnitTests(unittest.TestCase):
    """HTTP-level unit tests using Flask's unittest-friendly test client."""

    def setUp(self):
        """Configure a fresh temporary SQLite database for each test."""
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.database_uri = f"sqlite:///{Path(self.temp_db_path).as_posix()}"

        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SQLALCHEMY_DATABASE_URI=self.database_uri,
        )

        self.app_context = app.app_context()
        self.app_context.push()

        # Flask-SQLAlchemy caches the engine after app import, so rebind it
        # to this test's temp database before creating tables.
        try:
            db.engine.dispose()
        except Exception:
            pass
        db.engines[None] = create_engine(self.database_uri)
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

    def tearDown(self):
        """Drop the schema and delete the temporary SQLite file."""
        db.session.remove()
        db.drop_all()
        try:
            db.engine.dispose()
        except Exception:
            pass
        self.app_context.pop()

        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def make_user(self, username="alice", email=None, password="password123"):
        """Insert a User with sensible defaults; password is hashed."""
        user = User(
            username=username,
            email=email or f"{username}@example.com",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def make_movie(self, title="Test Movie", release_year=2020, genres=None, **kwargs):
        """Insert a Movie; genres can be passed as a list of names."""
        defaults = {"director_name": "Test Director"}
        defaults.update(kwargs)
        movie = Movie(title=title, release_year=release_year, **defaults)
        if genres:
            attached = []
            for name in genres:
                genre = db.session.query(Genre).filter_by(name=name).first()
                if genre is None:
                    genre = Genre(name=name)
                    db.session.add(genre)
                attached.append(genre)
            movie.genres = attached
        db.session.add(movie)
        db.session.commit()
        return movie

    def login(self, user_id):
        """Log the test client in by writing Flask-Login session keys."""
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user_id)
            sess["_fresh"] = True

    def test_signup_creates_user_with_hashed_password(self):
        """POST /signup should insert a User whose password is hashed."""
        response = self.client.post(
            "/signup",
            data={
                "username": "alice",
                "email": "alice@example.com",
                "password": "supersecret",
                "confirm_password": "supersecret",
            },
            follow_redirects=False,
        )

        self.assertIn(response.status_code, (200, 302))

        user = User.query.filter_by(email="alice@example.com").first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, "supersecret")
        self.assertTrue(user.check_password("supersecret"))

    def test_signup_rejects_duplicate_email(self):
        """A second signup with an existing email should return 409."""
        self.make_user(username="alice", email="alice@example.com")

        response = self.client.post(
            "/signup",
            data={
                "username": "alice_again",
                "email": "alice@example.com",
                "password": "anotherpassword",
                "confirm_password": "anotherpassword",
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_login_wrong_password_returns_401(self):
        """POST /login with the wrong password should return 401."""
        self.make_user(
            username="alice",
            email="alice@example.com",
            password="correct-password",
        )

        response = self.client.post(
            "/login",
            data={"email": "alice@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)

    def test_search_filters_by_genre(self):
        """/search?genre=Sci-Fi should show only Sci-Fi movies."""
        self.make_movie(title="Inception", genres=["Sci-Fi"])
        self.make_movie(title="Past Lives", genres=["Drama"])

        response = self.client.get("/search?genre=Sci-Fi")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Inception", response.data)
        self.assertNotIn(b"Past Lives", response.data)

    def test_search_min_rating_excludes_low_rated(self):
        """Movies with average rating below the threshold are filtered out."""
        high = self.make_movie(title="HighRated", genres=["Sci-Fi"])
        low = self.make_movie(title="LowRated", genres=["Sci-Fi"])
        reviewer = self.make_user(username="bob", email="bob@example.com")

        db.session.add(
            Review(user_id=reviewer.id, movie_id=high.id, rating=9, body="great")
        )
        db.session.add(
            Review(user_id=reviewer.id, movie_id=low.id, rating=4, body="meh")
        )
        db.session.commit()

        response = self.client.get("/search?min_rating=7%2B")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"HighRated", response.data)
        self.assertNotIn(b"LowRated", response.data)

    def test_review_duplicate_returns_409(self):
        """A user may only review each movie once; the second attempt is 409."""
        alice = self.make_user(username="alice", email="alice@example.com")
        movie = self.make_movie(title="Inception")
        self.login(alice.id)

        first_response = self.client.post(
            f"/movie/{movie.id}/review",
            data={"rating": "9", "body": "great"},
        )
        self.assertEqual(first_response.status_code, 201)

        second_response = self.client.post(
            f"/movie/{movie.id}/review",
            data={"rating": "7", "body": "changed my mind"},
        )
        self.assertEqual(second_response.status_code, 409)

    def test_review_non_owner_edit_returns_403(self):
        """A user trying to edit someone else's review should get 403."""
        alice = self.make_user(username="alice", email="alice@example.com")
        bob = self.make_user(username="bob", email="bob@example.com")
        movie = self.make_movie(title="Inception")

        review = Review(
            user_id=alice.id,
            movie_id=movie.id,
            rating=9,
            body="loved it",
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

        self.login(bob.id)
        response = self.client.post(
            f"/review/{review_id}/edit",
            data={"rating": "1", "body": "hijacked"},
        )

        self.assertEqual(response.status_code, 403)

    def test_watchlist_add_is_idempotent(self):
        """Re-adding a movie should not create a second WatchlistItem row."""
        alice = self.make_user(username="alice", email="alice@example.com")
        movie = self.make_movie(title="Inception")
        self.login(alice.id)

        first_response = self.client.post(f"/watchlist/add/{movie.id}")
        self.assertEqual(first_response.status_code, 201)
        self.assertTrue(first_response.get_json()["added"])

        second_response = self.client.post(f"/watchlist/add/{movie.id}")
        self.assertEqual(second_response.status_code, 200)
        self.assertTrue(second_response.get_json()["already_added"])

        count = WatchlistItem.query.filter_by(
            user_id=alice.id,
            movie_id=movie.id,
        ).count()
        self.assertEqual(count, 1)

    def test_like_review_increments_count(self):
        """POST /review/<id>/like should add a row and increment like_count."""
        alice = self.make_user(username="alice", email="alice@example.com")
        bob = self.make_user(username="bob", email="bob@example.com")
        movie = self.make_movie(title="Inception")

        review = Review(
            user_id=alice.id,
            movie_id=movie.id,
            rating=9,
            body="great",
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

        self.login(bob.id)
        response = self.client.post(f"/review/{review_id}/like")

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertTrue(body["liked"])
        self.assertEqual(body["like_count"], 1)

        like_rows = ReviewLike.query.filter_by(
            user_id=bob.id,
            review_id=review_id,
        ).count()
        self.assertEqual(like_rows, 1)

    def test_follow_self_returns_400(self):
        """POST /user/<own_id>/follow should be rejected with 400."""
        alice = self.make_user(username="alice", email="alice@example.com")
        self.login(alice.id)

        response = self.client.post(f"/user/{alice.id}/follow")

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertFalse(payload["ok"])
        self.assertIn("yourself", payload["error"].lower())


if __name__ == "__main__":
    unittest.main()
