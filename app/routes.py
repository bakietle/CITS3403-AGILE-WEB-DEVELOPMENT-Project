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
from app.forms import SearchForm
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


@app.route("/movie/<int:movie_id>")
def movie(movie_id):
    """Single movie detail page (hero + details sidebar)."""
    movie_obj = db.session.get(Movie, movie_id)
    if movie_obj is None:
        abort(404)
    return render_template("movie_page.html", movie=movie_obj)


# ─────────────────────────────────────────────────────────────────────────
# Module D — Watchlist
# ─────────────────────────────────────────────────────────────────────────
#
# Security rule: the user_id on each WatchlistItem is taken from
# current_user, NEVER from the request body / URL. The <movie_id> in the
# URL is what the user wants to add/remove; the user themselves comes
# from the session.

@app.route("/watchlist")
@login_required
def watchlist():
    """Render the current user's watchlist."""
    items = (
        WatchlistItem.query.filter_by(user_id=current_user.id)
        .order_by(WatchlistItem.created_at.desc())
        .all()
    )
    return render_template(
        "watchlist_page.html",
        watchlist_items=items,
        watchlist_count=len(items),
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
