"""Unit tests for the Movie Star Flask app.

Each module is exercised on at least one happy path and one error path
where applicable. Tests use a temp SQLite database (per fixtures in
conftest.py) and never touch the network.

Run with:

    pytest tests/test_unit.py -v
"""
from app import db
from app.models import Review, ReviewLike, User, WatchlistItem


# ──────────────────────────────────────────────────────────────────
# 1. Auth — signup stores password as a hash, not plaintext
# ──────────────────────────────────────────────────────────────────

def test_signup_creates_user_with_hashed_password(client, app):
    """POST /signup should insert a User whose password is hashed."""
    response = client.post(
        "/signup",
        data={
            "username": "alice",
            "email": "alice@example.com",
            "password": "supersecret",
            "confirm_password": "supersecret",
        },
        follow_redirects=False,
    )
    # On success the route redirects to /profile.
    assert response.status_code in (200, 302)

    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        assert user is not None
        # Password is hashed, never stored as plaintext.
        assert user.password_hash != "supersecret"
        assert user.check_password("supersecret") is True


# ──────────────────────────────────────────────────────────────────
# 2. Auth — signup rejects a duplicate email with 409
# ──────────────────────────────────────────────────────────────────

def test_signup_rejects_duplicate_email(client, make_user):
    """A second signup with an existing email should return 409."""
    make_user(username="alice", email="alice@example.com")

    response = client.post(
        "/signup",
        data={
            "username": "alice_again",
            "email": "alice@example.com",  # already taken
            "password": "anotherpassword",
            "confirm_password": "anotherpassword",
        },
    )
    assert response.status_code == 409


# ──────────────────────────────────────────────────────────────────
# 3. Auth — wrong password returns 401
# ──────────────────────────────────────────────────────────────────

def test_login_wrong_password_returns_401(client, make_user):
    """POST /login with the wrong password should return 401."""
    make_user(
        username="alice",
        email="alice@example.com",
        password="correct-password",
    )

    response = client.post(
        "/login",
        data={"email": "alice@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


# ──────────────────────────────────────────────────────────────────
# 4. Movies / Search — genre filter
# ──────────────────────────────────────────────────────────────────

def test_search_filters_by_genre(client, make_movie):
    """/search?genre=Sci-Fi should show only Sci-Fi movies."""
    make_movie(title="Inception", genres=["Sci-Fi"])
    make_movie(title="Past Lives", genres=["Drama"])

    response = client.get("/search?genre=Sci-Fi")
    assert response.status_code == 200
    assert b"Inception" in response.data
    assert b"Past Lives" not in response.data


# ──────────────────────────────────────────────────────────────────
# 5. Movies / Search — min_rating excludes low-rated movies
# ──────────────────────────────────────────────────────────────────

def test_search_min_rating_excludes_low_rated(
    client, app, make_user, make_movie,
):
    """Movies with average rating below the threshold are filtered out
    BEFORE pagination, so the rendered page only contains qualifying
    titles."""
    high = make_movie(title="HighRated", genres=["Sci-Fi"])
    low = make_movie(title="LowRated", genres=["Sci-Fi"])
    reviewer = make_user(username="bob", email="bob@example.com")

    with app.app_context():
        db.session.add(Review(
            user_id=reviewer.id, movie_id=high.id, rating=9, body="great",
        ))
        db.session.add(Review(
            user_id=reviewer.id, movie_id=low.id, rating=4, body="meh",
        ))
        db.session.commit()

    response = client.get("/search?min_rating=7%2B")
    assert response.status_code == 200
    assert b"HighRated" in response.data
    assert b"LowRated" not in response.data


# ──────────────────────────────────────────────────────────────────
# 6. Reviews — duplicate review on the same movie returns 409
# ──────────────────────────────────────────────────────────────────

def test_review_duplicate_returns_409(
    client, make_user, make_movie, login,
):
    """A user may only review each movie once; the second attempt is 409."""
    alice = make_user(username="alice", email="alice@example.com")
    movie = make_movie(title="Inception")
    login(alice.id)

    r1 = client.post(
        f"/movie/{movie.id}/review",
        data={"rating": "9", "body": "great"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        f"/movie/{movie.id}/review",
        data={"rating": "7", "body": "changed my mind"},
    )
    assert r2.status_code == 409


# ──────────────────────────────────────────────────────────────────
# 7. Reviews — non-owner editing returns 403
# ──────────────────────────────────────────────────────────────────

def test_review_non_owner_edit_returns_403(
    client, app, make_user, make_movie, login,
):
    """A user trying to edit someone else's review should get 403."""
    alice = make_user(username="alice", email="alice@example.com")
    bob = make_user(username="bob", email="bob@example.com")
    movie = make_movie(title="Inception")

    with app.app_context():
        review = Review(
            user_id=alice.id, movie_id=movie.id, rating=9, body="loved it",
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    # Bob tries to edit Alice's review.
    login(bob.id)
    response = client.post(
        f"/review/{review_id}/edit",
        data={"rating": "1", "body": "hijacked"},
    )
    assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# 8. Watchlist — add is idempotent
# ──────────────────────────────────────────────────────────────────

def test_watchlist_add_is_idempotent(
    client, app, make_user, make_movie, login,
):
    """Re-adding a movie should not create a second WatchlistItem row."""
    alice = make_user(username="alice", email="alice@example.com")
    movie = make_movie(title="Inception")
    login(alice.id)

    r1 = client.post(f"/watchlist/add/{movie.id}")
    assert r1.status_code == 201
    assert r1.get_json()["added"] is True

    r2 = client.post(f"/watchlist/add/{movie.id}")
    assert r2.status_code == 200
    assert r2.get_json()["already_added"] is True

    with app.app_context():
        count = WatchlistItem.query.filter_by(
            user_id=alice.id, movie_id=movie.id,
        ).count()
        assert count == 1  # not 2


# ──────────────────────────────────────────────────────────────────
# 9. Likes — liking a review increments like_count
# ──────────────────────────────────────────────────────────────────

def test_like_review_increments_count(
    client, app, make_user, make_movie, login,
):
    """POST /review/<id>/like should add a row and increment like_count."""
    alice = make_user(username="alice", email="alice@example.com")
    bob = make_user(username="bob", email="bob@example.com")
    movie = make_movie(title="Inception")

    with app.app_context():
        review = Review(
            user_id=alice.id, movie_id=movie.id, rating=9, body="great",
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id

    login(bob.id)
    response = client.post(f"/review/{review_id}/like")
    assert response.status_code == 201
    body = response.get_json()
    assert body["liked"] is True
    assert body["like_count"] == 1

    # And the DB now has a ReviewLike row.
    with app.app_context():
        like_rows = ReviewLike.query.filter_by(
            user_id=bob.id, review_id=review_id,
        ).count()
        assert like_rows == 1


# ──────────────────────────────────────────────────────────────────
# 10. Profile — cannot follow yourself
# ──────────────────────────────────────────────────────────────────

def test_follow_self_returns_400(client, make_user, login):
    """POST /user/<own_id>/follow should be rejected with 400."""
    alice = make_user(username="alice", email="alice@example.com")
    login(alice.id)

    response = client.post(f"/user/{alice.id}/follow")
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["ok"] is False
    assert "yourself" in payload["error"].lower()
