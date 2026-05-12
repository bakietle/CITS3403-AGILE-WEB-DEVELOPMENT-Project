"""Page routes for Module B (Movies + Search) and shared page shells.

Module B owns the server-rendered pages backed by real Movie data:

    GET /            home page (hero search + highest-rated grid)
    GET /home        same as /
    GET /search      search results with filters + pagination
    GET /movie/<id>  single-movie detail page

Routes for other modules are still thin shells until those modules
implement their own queries. They're listed at the bottom of this file.
Private routes (watchlist, profile) carry @login_required from Module A.

Notes for teammates:
    - The "Popular Reviews" section on the home page currently renders
      recently-added movies as a placeholder. Question N2 in the team
      discussion issue is still open about whether this should be
      review snippets (Module C) or trending movies (Module B).
    - Movie detail page only ships the hero + details sidebar from this
      module. The write-review form and community reviews list belong
      to Module C.
"""
from flask import abort, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app import app, db
from app.forms import ReviewForm, SearchForm
from app.models import Genre, Movie, Review, WatchlistItem


# Display constants — adjust here if the design tweaks them.
HOME_HIGHLIGHT_LIMIT = 8       # Highest-rated grid on the home page.
HOME_SECONDARY_LIMIT = 6       # Secondary "Popular Reviews" / trending row.
SEARCH_PAGE_SIZE = 20          # Movies per search result page.


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _highest_rated_movies(limit, min_reviews=0):
    """Return movies ordered by their average rating (descending).

    Computed in Python so we can reuse Movie.average_rating without writing
    the SQL aggregation by hand. Movies with fewer than `min_reviews`
    reviews are excluded; ties fall back to creation order.
    """
    movies = Movie.query.all()
    eligible = [m for m in movies if len(m.reviews) >= min_reviews]
    eligible.sort(
        key=lambda m: (m.average_rating or 0, m.created_at),
        reverse=True,
    )
    return eligible[:limit]


def _parse_min_rating(raw):
    """Convert a min-rating dropdown value (e.g. '7+') into an int threshold."""
    if not raw or raw == "Any":
        return None
    try:
        return int(raw.rstrip("+"))
    except (ValueError, AttributeError):
        return None


# ─────────────────────────────────────────────────────────────────────────
# Pages owned by Module B
# ─────────────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/home")
def home():
    """Home page: hero search + highest-rated grid + secondary row."""
    highlight_movies = _highest_rated_movies(limit=HOME_HIGHLIGHT_LIMIT)

    # Until the team confirms what "Popular Reviews" should be, fill with
    # the most recently added movies as a placeholder.
    secondary_movies = (
        Movie.query.order_by(Movie.created_at.desc())
        .limit(HOME_SECONDARY_LIMIT)
        .all()
    )

    return render_template(
        "home_page.html",
        highlight_movies=highlight_movies,
        secondary_movies=secondary_movies,
    )


@app.route("/search")
def search():
    """Search results with genre/year/min-rating filters + pagination.

    All inputs come from the query string so URLs stay bookmarkable.
    Filtering is done at the DB level where possible; min_rating is
    applied in Python because it depends on a derived average across
    related rows.
    """
    # Bind the form to request.args so the template can render selected values.
    form = SearchForm(request.args)

    q = (request.args.get("q") or "").strip()
    genre = (request.args.get("genre") or "All").strip()
    year = request.args.get("year", type=int)
    min_rating_raw = (request.args.get("min_rating") or "Any").strip()
    page = request.args.get("page", default=1, type=int)

    # Build the base query.
    query = Movie.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Movie.title.ilike(like),
                Movie.director_name.ilike(like),
                Movie.cast_text.ilike(like),
            )
        )

    if genre and genre != "All":
        query = query.join(Movie.genres).filter(Genre.name == genre)

    if year:
        query = query.filter(Movie.release_year == year)

    # min_rating is a derived value (AVG of related reviews). Apply at the
    # DB level via a subquery joined on movie_id, BEFORE pagination, so the
    # result count and page links reflect the filtered set correctly.
    threshold = _parse_min_rating(min_rating_raw)
    if threshold is not None:
        avg_subq = (
            db.session.query(
                Review.movie_id.label("movie_id"),
                func.avg(Review.rating).label("avg_rating"),
            )
            .group_by(Review.movie_id)
            .subquery()
        )
        query = query.join(
            avg_subq, Movie.id == avg_subq.c.movie_id
        ).filter(avg_subq.c.avg_rating >= threshold)

    query = query.order_by(Movie.release_year.desc(), Movie.title.asc())

    # Paginate at the DB level. error_out=False -> empty page instead of 404.
    pagination = query.paginate(
        page=page, per_page=SEARCH_PAGE_SIZE, error_out=False
    )

    movies = pagination.items

    # Genre chips are rendered from the DB so they always match seed data.
    all_genres = Genre.query.order_by(Genre.name.asc()).all()

    return render_template(
        "searchresult_page.html",
        form=form,
        movies=movies,
        pagination=pagination,
        all_genres=all_genres,
        active_query=q,
        active_genre=genre,
        active_year=year,
        active_min_rating=min_rating_raw,
        total_results=pagination.total,
    )


REVIEW_SORTS = ("recent", "highest", "lowest")


@app.route("/movie/<int:movie_id>")
def movie(movie_id):
    """Single movie detail page (hero + details sidebar + reviews).

    The review section is rendered with these pieces of context:
      * `user_review`     — current user's own review on this movie (or None)
      * `reviews`         — everyone else's reviews
      * `review_form`     — fresh ReviewForm bound for create/edit submission
      * `active_sort`     — one of 'recent' (default) / 'highest' / 'lowest'

    The sort applies only to community reviews; the user's own review
    always sits at the top regardless.
    """
    movie_obj = db.session.get(Movie, movie_id)
    if movie_obj is None:
        abort(404)

    sort = (request.args.get("sort") or "recent").strip().lower()
    if sort not in REVIEW_SORTS:
        sort = "recent"

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            user_id=current_user.id, movie_id=movie_id
        ).first()

    # Community reviews — exclude the current user's own review since it's
    # shown separately at the top under "Your Review".
    others_query = Review.query.filter_by(movie_id=movie_id)
    if user_review is not None:
        others_query = others_query.filter(Review.id != user_review.id)

    # Newest first is the tiebreaker for all rating-based sorts.
    if sort == "highest":
        others_query = others_query.order_by(
            Review.rating.desc(), Review.created_at.desc()
        )
    elif sort == "lowest":
        others_query = others_query.order_by(
            Review.rating.asc(), Review.created_at.desc()
        )
    else:  # recent (default)
        others_query = others_query.order_by(Review.created_at.desc())

    reviews = others_query.all()
    review_form = ReviewForm()

    return render_template(
        "movie_page.html",
        movie=movie_obj,
        reviews=reviews,
        user_review=user_review,
        review_form=review_form,
        community_count=len(reviews),
        active_sort=sort,
    )


# ─────────────────────────────────────────────────────────────────────────
# Module D — Watchlist
# ─────────────────────────────────────────────────────────────────────────
#
# Security rule: the user_id on each WatchlistItem is taken from
# current_user, NEVER from the request body / URL. The <movie_id> in the
# URL is what the user wants to add/remove; the user themselves comes
# from the session.

WATCHLIST_SORTS = ("date", "rating", "title", "year")


def _sorted_watchlist_items(items, sort):
    """Sort watchlist items in Python.

    Average rating is a derived property over related Review rows, so doing
    this in Python keeps the route simple and avoids per-sort SQL changes.
    Watchlists are per-user and typically small, so the cost is negligible.
    """
    if sort == "title":
        items.sort(key=lambda i: (i.movie.title or "").lower())
    elif sort == "year":
        items.sort(key=lambda i: i.movie.release_year or 0, reverse=True)
    elif sort == "rating":
        items.sort(key=lambda i: i.movie.average_rating or -1, reverse=True)
    else:  # "date" — default. Newest additions first.
        items.sort(key=lambda i: i.created_at, reverse=True)
    return items


@app.route("/watchlist")
@login_required
def watchlist():
    """Render the current user's watchlist.

    Supports ?sort=date|rating|title|year to reorder the cards. Unknown
    values fall back to date (newest first).
    """
    sort = (request.args.get("sort") or "date").strip().lower()
    if sort not in WATCHLIST_SORTS:
        sort = "date"

    items = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    items = _sorted_watchlist_items(items, sort)

    return render_template(
        "watchlist_page.html",
        watchlist_items=items,
        watchlist_count=len(items),
        active_sort=sort,
    )


@app.route("/watchlist/add/<int:movie_id>", methods=["POST"])
@login_required
def watchlist_add(movie_id):
    """Add a movie to the current user's watchlist.

    Idempotent: if the movie is already on the watchlist, returns OK
    without creating a duplicate (the model has a UniqueConstraint that
    would raise IntegrityError otherwise).
    """
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        return jsonify(ok=False, error="Movie not found."), 404

    existing = WatchlistItem.query.filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if existing is not None:
        return jsonify(ok=True, already_added=True)

    item = WatchlistItem(user_id=current_user.id, movie_id=movie_id)
    db.session.add(item)
    db.session.commit()
    return jsonify(ok=True, added=True), 201


@app.route("/watchlist/remove/<int:movie_id>", methods=["POST"])
@login_required
def watchlist_remove(movie_id):
    """Remove a movie from the current user's watchlist."""
    item = WatchlistItem.query.filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if item is None:
        return jsonify(ok=False, error="Not in your watchlist."), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify(ok=True, removed=True)


# ─────────────────────────────────────────────────────────────────────────
# Module C — Reviews
# ─────────────────────────────────────────────────────────────────────────
#
# Authorisation rule for edit / delete:
#
#     if review.user_id != current_user.id:
#         abort(403)
#
# Endpoints are AJAX-friendly (return JSON, expect form-data with the
# CSRF token in X-CSRFToken header or as csrf_token form field).


def _review_to_json(review):
    """Shape a Review for JSON responses."""
    return {
        "id": review.id,
        "movie_id": review.movie_id,
        "user_id": review.user_id,
        "username": review.user.username if review.user else None,
        "rating": review.rating,
        "body": review.body,
        "contains_spoilers": review.contains_spoilers,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None,
    }


def _first_form_error(form):
    """Return the first user-facing validation error message on a form."""
    for messages in form.errors.values():
        if messages:
            return messages[0]
    return "Invalid submission."


@app.route("/movie/<int:movie_id>/review", methods=["POST"])
@login_required
def review_create(movie_id):
    """Create a new review on the given movie for the current user."""
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        return jsonify(ok=False, error="Movie not found."), 404

    # The model has UniqueConstraint(user_id, movie_id) so we reject
    # duplicates explicitly with 409 instead of letting it raise an
    # IntegrityError on commit.
    existing = Review.query.filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if existing is not None:
        return (
            jsonify(
                ok=False,
                error="You have already reviewed this movie. Use the edit endpoint instead.",
                existing_review_id=existing.id,
            ),
            409,
        )

    form = ReviewForm()
    if not form.validate_on_submit():
        return (
            jsonify(ok=False, error=_first_form_error(form), errors=form.errors),
            400,
        )

    review = Review(
        user_id=current_user.id,
        movie_id=movie_id,
        rating=form.rating.data,
        body=form.body.data.strip(),
        contains_spoilers=bool(form.contains_spoilers.data),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(ok=True, review=_review_to_json(review)), 201


@app.route("/review/<int:review_id>/edit", methods=["POST"])
@login_required
def review_edit(review_id):
    """Edit one of the current user's own reviews.

    A user who is not the review's author is rejected with 403, so this
    cannot be used to modify someone else's review.
    """
    review = db.session.get(Review, review_id)
    if review is None:
        return jsonify(ok=False, error="Review not found."), 404
    if review.user_id != current_user.id:
        abort(403)

    form = ReviewForm()
    if not form.validate_on_submit():
        return (
            jsonify(ok=False, error=_first_form_error(form), errors=form.errors),
            400,
        )

    review.rating = form.rating.data
    review.body = form.body.data.strip()
    review.contains_spoilers = bool(form.contains_spoilers.data)
    # updated_at is filled automatically by the model's onupdate hook.
    db.session.commit()
    return jsonify(ok=True, review=_review_to_json(review))


@app.route("/review/<int:review_id>/delete", methods=["POST"])
@login_required
def review_delete(review_id):
    """Delete one of the current user's own reviews."""
    review = db.session.get(Review, review_id)
    if review is None:
        return jsonify(ok=False, error="Review not found."), 404
    if review.user_id != current_user.id:
        abort(403)

    db.session.delete(review)
    db.session.commit()
    # Related likes + comments are cascaded away by the model's cascade rules.
    return jsonify(ok=True, deleted=True)


# ─────────────────────────────────────────────────────────────────────────
# Pages owned by other modules — kept as thin shells until they take over.
# Private routes are protected with @login_required (Module A).
# ─────────────────────────────────────────────────────────────────────────

@app.route("/profile")
@login_required
def profile():
    return render_template("my_profile.html")


@app.route("/user/<int:user_id>")
def user_profile(user_id):
    return render_template("other_profile.html")
