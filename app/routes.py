"""Page routes for Module B (Movies + Search).

These are the server-rendered (SSR) pages owned by the movies/search module:

    GET /            home page (hero search + highest-rated grid)
    GET /home        same as /
    GET /search      search results with filters + pagination
    GET /movie/<id>  single-movie detail page

Other modules (auth, reviews, watchlist, profile) own their own routes
defined in their respective files.

Notes for teammates:
    - The "Popular Reviews" section on the home page currently renders
      recently-added movies as a placeholder. Question N2 in the team
      discussion issue is still open about whether this should be
      review snippets (Module C) or trending movies (Module B).
    - Movie detail page only ships the hero + details sidebar from this
      module. The write-review form and community reviews list belong
      to Module C.
"""
from flask import render_template, request

from app import app, db
from app.forms import SearchForm
from app.models import Genre, Movie


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
# Pages
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

    query = query.order_by(Movie.release_year.desc(), Movie.title.asc())

    # Paginate at the DB level. error_out=False -> empty page instead of 404.
    pagination = query.paginate(
        page=page, per_page=SEARCH_PAGE_SIZE, error_out=False
    )

    # min_rating is a derived value, so filter the page items in Python.
    threshold = _parse_min_rating(min_rating_raw)
    if threshold is not None:
        movies = [
            m for m in pagination.items
            if (m.average_rating or 0) >= threshold
        ]
    else:
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
        # 404 will use Flask's default handler unless someone adds a custom one.
        from flask import abort
        abort(404)
    return render_template("movie_page.html", movie=movie_obj)


# ─────────────────────────────────────────────────────────────────────────
# Pages owned by other modules — kept as thin shells until they take over.
# ─────────────────────────────────────────────────────────────────────────

@app.route("/watchlist")
def watchlist():
    return render_template("watchlist_page.html")


@app.route("/profile")
def profile():
    return render_template("my_profile.html")


@app.route("/user/<int:user_id>")
def user_profile(user_id):
    return render_template("other_profile.html")
