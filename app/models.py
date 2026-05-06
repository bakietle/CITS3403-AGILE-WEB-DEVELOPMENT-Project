"""SQLAlchemy models for the Movie Star app.

Schema follows the project's design document — nine tables in total:

    1. users               6. watchlist_items
    2. movies              7. review_likes
    3. genres              8. follows
    4. movie_genres        9. review_comments
    5. reviews
"""
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


# ─────────────────────────────────────────────
# 4. movie_genres  (pure join table — no extra columns)
# ─────────────────────────────────────────────
# Defined first so that Movie.genres / Genre.movies can reference it.

movie_genres = db.Table(
    "movie_genres",
    db.Column("movie_id", db.Integer, db.ForeignKey("movies.id"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id"), primary_key=True),
)


# ─────────────────────────────────────────────
# 1. users
# ─────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avatar_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # ── Relationships ────────────────────────
    reviews = db.relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )
    watchlist = db.relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "ReviewComment", back_populates="user", cascade="all, delete-orphan"
    )

    # Self-referential follow relationship via the Follow association model.
    # `user.followed.append(other)` creates a Follow row (with `created_at`
    # auto-populated by its default).
    followed = db.relationship(
        "User",
        secondary="follows",
        primaryjoin="User.id == Follow.follower_id",
        secondaryjoin="User.id == Follow.followed_id",
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    # ── Password helpers ─────────────────────
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ── Stats / helpers ──────────────────────
    @property
    def review_count(self):
        return len(self.reviews)

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return self.followed.count()

    @property
    def average_rating(self):
        """Average rating this user has given across all their reviews."""
        if not self.reviews:
            return None
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    def is_following(self, other):
        return self.followed.filter(Follow.followed_id == other.id).count() > 0

    def follow(self, other):
        if other.id != self.id and not self.is_following(other):
            self.followed.append(other)

    def unfollow(self, other):
        if self.is_following(other):
            self.followed.remove(other)

    def __repr__(self):
        return f"<User {self.username}>"


# ─────────────────────────────────────────────
# 2. movies
# ─────────────────────────────────────────────

class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    release_year = db.Column(db.Integer, nullable=True, index=True)
    release_date = db.Column(db.Date, nullable=True)
    runtime_minutes = db.Column(db.Integer, nullable=True)
    age_rating = db.Column(db.String(20), nullable=True)
    synopsis = db.Column(db.Text, nullable=True)
    poster_path = db.Column(db.String(255), nullable=True)
    backdrop_path = db.Column(db.String(255), nullable=True)
    director_name = db.Column(db.String(120), nullable=True)
    cast_text = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # ── Relationships ────────────────────────
    reviews = db.relationship(
        "Review", back_populates="movie", cascade="all, delete-orphan"
    )

    watchlist_items = db.relationship(
        "WatchlistItem", back_populates="movie", cascade="all, delete-orphan"
    )

    genres = db.relationship(
        "Genre", secondary=movie_genres, back_populates="movies"
    )

    # ── Helpers ──────────────────────────────
    @property
    def genre_list(self):
        return [g.name for g in self.genres]

    @property
    def primary_genre(self):
        return self.genres[0].name if self.genres else ""

    @property
    def average_rating(self):
        if not self.reviews:
            return None
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    @property
    def runtime_pretty(self):
        if not self.runtime_minutes:
            return ""
        hours, minutes = divmod(self.runtime_minutes, 60)
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"

    @property
    def release_date_pretty(self):
        if self.release_date:
            return self.release_date.strftime("%d %B %Y")
        return ""

    def __repr__(self):
        return f"<Movie {self.title} ({self.release_year})>"


# ─────────────────────────────────────────────
# 3. genres
# ─────────────────────────────────────────────

class Genre(db.Model):
    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)

    movies = db.relationship(
        "Movie", secondary=movie_genres, back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre {self.name}>"


# ─────────────────────────────────────────────
# 5. reviews
# ─────────────────────────────────────────────

class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True
    )
    rating = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=False)
    contains_spoilers = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="reviews")
    movie = db.relationship("Movie", back_populates="reviews")

    # Likes through the ReviewLike association model.
    liked_by = db.relationship(
        "User",
        secondary="review_likes",
        backref="liked_reviews",
        viewonly=False,
    )

    comments = db.relationship(
        "ReviewComment", back_populates="review", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_review_user_movie"),
        CheckConstraint("rating >= 1 AND rating <= 10", name="ck_review_rating_range"),
    )

    @property
    def like_count(self):
        return len(self.liked_by)

    def is_liked_by(self, user):
        if user is None or not user.is_authenticated:
            return False
        return user in self.liked_by

    @property
    def top_level_comments(self):
        """Comments at the root of the thread, ordered oldest first."""
        return [c for c in self.comments if c.parent_comment_id is None and not c.is_deleted]

    def __repr__(self):
        return f"<Review user={self.user_id} movie={self.movie_id} rating={self.rating}>"


# ─────────────────────────────────────────────
# 6. watchlist_items
# ─────────────────────────────────────────────

class WatchlistItem(db.Model):
    __tablename__ = "watchlist_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(280), nullable=True)

    user = db.relationship("User", back_populates="watchlist")
    movie = db.relationship("Movie", back_populates = "watchlist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_watchlist_user_movie"),
    )

    def __repr__(self):
        return f"<WatchlistItem user={self.user_id} movie={self.movie_id}>"


# ─────────────────────────────────────────────
# 7. review_likes
# ─────────────────────────────────────────────

class ReviewLike(db.Model):
    __tablename__ = "review_likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    review_id = db.Column(
        db.Integer, db.ForeignKey("reviews.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "review_id", name="uq_like_user_review"),
    )

    def __repr__(self):
        return f"<ReviewLike user={self.user_id} review={self.review_id}>"


# ─────────────────────────────────────────────
# 8. follows
# ─────────────────────────────────────────────

class Follow(db.Model):
    __tablename__ = "follows"

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    followed_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("follower_id", "followed_id", name="uq_follow_pair"),
        CheckConstraint("follower_id != followed_id", name="ck_follow_no_self"),
    )

    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.followed_id}>"


# ─────────────────────────────────────────────
# 9. review_comments
# ─────────────────────────────────────────────

class ReviewComment(db.Model):
    __tablename__ = "review_comments"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(
        db.Integer, db.ForeignKey("reviews.id"), nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    parent_comment_id = db.Column(
        db.Integer, db.ForeignKey("review_comments.id"), nullable=True
    )
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    review = db.relationship("Review", back_populates="comments")
    user = db.relationship("User", back_populates="comments")

    # Self-referential — replies to this comment.
    replies = db.relationship(
        "ReviewComment",
        backref=db.backref("parent_comment", remote_side="ReviewComment.id"),
        cascade="all, delete-orphan",
    )

    @property
    def display_body(self):
        """Body to show in the UI; respects soft-delete to keep thread structure."""
        return "[comment removed]" if self.is_deleted else self.body

    def __repr__(self):
        return f"<ReviewComment review={self.review_id} user={self.user_id}>"


# ─────────────────────────────────────────────
# Flask-Login user loader
# ─────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None