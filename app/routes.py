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
from collections import Counter

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app import app, db
from app.forms import CommentForm, ProfileEditForm, ReviewForm, SearchForm
from app.models import (
    Follow,
    Genre,
    Movie,
    Review,
    ReviewComment,
    ReviewLike,
    User,
    WatchlistItem,
)


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
    comment_form = CommentForm()

    return render_template(
        "movie_page.html",
        movie=movie_obj,
        reviews=reviews,
        user_review=user_review,
        review_form=review_form,
        comment_form=comment_form,
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


@app.route("/review/<int:review_id>/like", methods=["POST"])
@login_required
def review_like(review_id):
    """Like a review on behalf of the current user.

    Idempotent: re-liking returns 200 with already_liked=True rather than
    blowing up on the UniqueConstraint(user_id, review_id) of ReviewLike.
    A user is allowed to like their own review (no self-vote restriction).
    """
    review = db.session.get(Review, review_id)
    if review is None:
        return jsonify(ok=False, error="Review not found."), 404

    existing = ReviewLike.query.filter_by(
        user_id=current_user.id, review_id=review_id
    ).first()
    if existing is not None:
        return jsonify(
            ok=True, already_liked=True, like_count=review.like_count
        )

    like = ReviewLike(user_id=current_user.id, review_id=review_id)
    db.session.add(like)
    db.session.commit()
    return jsonify(ok=True, liked=True, like_count=review.like_count), 201


@app.route("/review/<int:review_id>/unlike", methods=["POST"])
@login_required
def review_unlike(review_id):
    """Remove the current user's like on a review."""
    review = db.session.get(Review, review_id)
    if review is None:
        return jsonify(ok=False, error="Review not found."), 404

    like = ReviewLike.query.filter_by(
        user_id=current_user.id, review_id=review_id
    ).first()
    if like is None:
        return jsonify(ok=False, error="You have not liked this review."), 404

    db.session.delete(like)
    db.session.commit()
    return jsonify(ok=True, unliked=True, like_count=review.like_count)


def _comment_to_json(comment):
    """Shape a ReviewComment for JSON responses."""
    return {
        "id": comment.id,
        "review_id": comment.review_id,
        "user_id": comment.user_id,
        "username": comment.user.username if comment.user else None,
        "parent_comment_id": comment.parent_comment_id,
        "body": comment.display_body,
        "is_deleted": comment.is_deleted,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


@app.route("/review/<int:review_id>/comment", methods=["POST"])
@login_required
def comment_create(review_id):
    """Add a top-level comment on a review."""
    review = db.session.get(Review, review_id)
    if review is None:
        return jsonify(ok=False, error="Review not found."), 404

    form = CommentForm()
    if not form.validate_on_submit():
        return (
            jsonify(ok=False, error=_first_form_error(form), errors=form.errors),
            400,
        )

    comment = ReviewComment(
        review_id=review_id,
        user_id=current_user.id,
        body=form.body.data,
        parent_comment_id=None,
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify(ok=True, comment=_comment_to_json(comment)), 201


@app.route("/comment/<int:comment_id>/reply", methods=["POST"])
@login_required
def comment_reply(comment_id):
    """Reply to an existing comment (threaded via parent_comment_id)."""
    parent = db.session.get(ReviewComment, comment_id)
    if parent is None:
        return jsonify(ok=False, error="Comment not found."), 404

    # The template renders at most two visual levels (top-level comment
    # + one row of replies). Reject attempts to reply to a reply so the
    # DB never accumulates rows the UI cannot show.
    if parent.parent_comment_id is not None:
        return (
            jsonify(
                ok=False,
                error="Replies can only be posted on top-level comments.",
            ),
            400,
        )

    form = CommentForm()
    if not form.validate_on_submit():
        return (
            jsonify(ok=False, error=_first_form_error(form), errors=form.errors),
            400,
        )

    reply = ReviewComment(
        review_id=parent.review_id,
        user_id=current_user.id,
        body=form.body.data,
        parent_comment_id=parent.id,
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify(ok=True, comment=_comment_to_json(reply)), 201


@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def comment_delete(comment_id):
    """Soft-delete one of the current user's own comments.

    We don't hard-delete because the row may be a parent of replies; the
    template renders display_body which substitutes '[comment removed]'
    for soft-deleted comments so the thread structure stays intact.
    """
    comment = db.session.get(ReviewComment, comment_id)
    if comment is None:
        return jsonify(ok=False, error="Comment not found."), 404
    if comment.user_id != current_user.id:
        abort(403)

    comment.is_deleted = True
    db.session.commit()
    return jsonify(ok=True, deleted=True)


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
# Module E — Profile + Follow
# ─────────────────────────────────────────────────────────────────────────


def _top_genres_for(user, limit=4):
    """Compute the user's favourite genres by counting genre tags across
    all the movies they've reviewed. Returns a list of (name, count)."""
    counter = Counter()
    for review in user.reviews:
        if review.movie is None:
            continue
        for g in review.movie.genres:
            counter[g.name] += 1
    return counter.most_common(limit)


@app.route("/profile")
@login_required
def profile():
    """Render the current user's own profile page."""
    user = current_user
    reviews = (
        Review.query.filter_by(user_id=user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    watchlist_count = WatchlistItem.query.filter_by(user_id=user.id).count()
    liked_count = (
        ReviewLike.query.filter_by(user_id=user.id).count()
    )
    return render_template(
        "my_profile.html",
        user=user,
        reviews=reviews,
        watchlist_count=watchlist_count,
        liked_count=liked_count,
        favourite_genres=_top_genres_for(user),
    )


@app.route("/user/<int:user_id>")
def user_profile(user_id):
    """Public profile page for any user.

    If a logged-in user lands on their own /user/<id> URL we redirect to
    /profile so the 'edit your profile' affordances show up correctly.
    """
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if current_user.is_authenticated and current_user.id == user.id:
        return redirect(url_for("profile"))

    reviews = (
        Review.query.filter_by(user_id=user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    is_following = (
        current_user.is_authenticated and current_user.is_following(user)
    )
    return render_template(
        "other_profile.html",
        user=user,
        reviews=reviews,
        is_following=is_following,
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    """Edit the current user's profile.

    GET renders the form pre-filled with existing values; POST validates
    and persists. Username uniqueness is checked here because it depends
    on DB state we don't want to bake into the form class.
    """
    form = ProfileEditForm()

    if request.method == "GET":
        form.username.data = current_user.username
        form.bio.data = current_user.bio or ""
        form.avatar_path.data = current_user.avatar_path or ""
        return render_template("profile_edit.html", form=form)

    # POST
    if not form.validate_on_submit():
        return (
            render_template("profile_edit.html", form=form),
            400,
        )

    new_username = form.username.data
    if new_username != current_user.username:
        clash = db.session.scalar(
            db.select(User).where(User.username == new_username)
        )
        if clash is not None:
            form.username.errors.append("That username is already taken.")
            return render_template("profile_edit.html", form=form), 409

    current_user.username = new_username
    current_user.bio = form.bio.data or None
    current_user.avatar_path = form.avatar_path.data or None
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("profile"))


@app.route("/user/<int:user_id>/follow", methods=["POST"])
@login_required
def user_follow(user_id):
    """Follow another user. Idempotent."""
    target = db.session.get(User, user_id)
    if target is None:
        return jsonify(ok=False, error="User not found."), 404
    if target.id == current_user.id:
        return jsonify(ok=False, error="You cannot follow yourself."), 400

    if current_user.is_following(target):
        return jsonify(
            ok=True,
            already_following=True,
            follower_count=target.follower_count,
        )

    current_user.follow(target)
    db.session.commit()
    return (
        jsonify(
            ok=True,
            following=True,
            follower_count=target.follower_count,
        ),
        201,
    )


@app.route("/user/<int:user_id>/unfollow", methods=["POST"])
@login_required
def user_unfollow(user_id):
    """Stop following another user."""
    target = db.session.get(User, user_id)
    if target is None:
        return jsonify(ok=False, error="User not found."), 404

    if not current_user.is_following(target):
        return (
            jsonify(ok=False, error="You are not following this user."),
            404,
        )

    current_user.unfollow(target)
    db.session.commit()
    return jsonify(
        ok=True,
        unfollowed=True,
        follower_count=target.follower_count,
    )
