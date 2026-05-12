"""WTForms definitions for the Movie Star app.

Each module owner should add their own form classes to this file (or to a
sub-package later if it grows too large). Forms here are server-side
schemas: they validate inputs, render CSRF tokens, and integrate with the
Flask request lifecycle.

Currently contains:
    - LoginForm        (Module A - Auth)
    - SignupForm       (Module A - Auth)
    - SearchForm       (Module B - Movies + Search)
    - ReviewForm       (Module C - Reviews)
    - CommentForm      (Module C - Comments on reviews)
    - ProfileEditForm  (Module E - Profile)
"""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Optional,
)


# ─────────────────────────────────────────────────────────────────────
# Module A — Authentication forms
# ─────────────────────────────────────────────────────────────────────

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Please enter your password.")],
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Enter the Stage")


class SignupForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Please choose a username."),
            Length(
                min=3,
                max=64,
                message="Username must be between 3 and 64 characters.",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address."),
            Length(max=120, message="Email must be 120 characters or fewer."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter a password."),
            Length(min=8, message="Password must be at least 8 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Join Movie Star")


# ─────────────────────────────────────────────────────────────────────
# Module B — Search form
# ─────────────────────────────────────────────────────────────────────

# Min-rating dropdown values shown on the search page.
MIN_RATING_CHOICES = [
    ("Any", "Any"),
    ("5+", "5+"),
    ("6+", "6+"),
    ("7+", "7+"),
    ("8+", "8+"),
    ("9+", "9+"),
]


class SearchForm(FlaskForm):
    """Search + filter form used on /search.

    Submitted as GET so URLs are bookmarkable / shareable. CSRF is disabled
    on this form because it's read-only — no state change happens on
    submission, so a token would only get in the way of pagination links.
    """

    class Meta:
        # Disable CSRF for GET-only search form.
        csrf = False

    q = StringField(
        "Query",
        validators=[Optional(), Length(max=200)],
    )

    genre = StringField(
        "Genre",
        validators=[Optional(), Length(max=50)],
        default="All",
    )

    year = IntegerField(
        "Release Year",
        validators=[Optional(), NumberRange(min=1888, max=2100)],
    )

    min_rating = SelectField(
        "Minimum Rating",
        choices=MIN_RATING_CHOICES,
        validators=[Optional()],
        default="Any",
    )


# ─────────────────────────────────────────────────────────────────────
# Module C — Review form
# ─────────────────────────────────────────────────────────────────────

REVIEW_BODY_MAX = 2000


class ReviewForm(FlaskForm):
    """Create or edit a review.

    Used by both POST /movie/<id>/review and POST /review/<id>/edit, so
    it has no submit button — it's submitted via AJAX, not via a regular
    HTML form submit.

    Validation mirrors the DB CheckConstraint on Review.rating (1..10)
    and a sensible 2000-char ceiling on body. CSRF is provided by the
    global CSRFProtect — AJAX callers must send X-CSRFToken header or
    include csrf_token as a form field.
    """

    rating = IntegerField(
        "Rating",
        validators=[
            InputRequired(message="Please choose a rating from 1 to 10."),
            NumberRange(min=1, max=10, message="Rating must be between 1 and 10."),
        ],
    )
    body = TextAreaField(
        "Review",
        # Strip surrounding whitespace BEFORE validators run, so a body of
        # "   " collapses to "" and is rejected by DataRequired instead of
        # silently being stored as empty after the route's own .strip().
        filters=[lambda v: v.strip() if isinstance(v, str) else v],
        validators=[
            DataRequired(message="Please write a review."),
            Length(
                min=1,
                max=REVIEW_BODY_MAX,
                message=f"Review must be {REVIEW_BODY_MAX} characters or fewer.",
            ),
        ],
    )
    contains_spoilers = BooleanField("Contains spoilers")


# Comment form is shared by both POST /review/<id>/comment and
# POST /comment/<id>/reply — same payload shape (body only), only the
# route differs.

COMMENT_BODY_MAX = 1000


class CommentForm(FlaskForm):
    """Create a comment on a review or a reply to an existing comment."""

    body = TextAreaField(
        "Comment",
        filters=[lambda v: v.strip() if isinstance(v, str) else v],
        validators=[
            DataRequired(message="Please write a comment."),
            Length(
                min=1,
                max=COMMENT_BODY_MAX,
                message=f"Comment must be {COMMENT_BODY_MAX} characters or fewer.",
            ),
        ],
    )


# ─────────────────────────────────────────────────────────────────────
# Module E — Profile edit form
# ─────────────────────────────────────────────────────────────────────

PROFILE_BIO_MAX = 500
PROFILE_AVATAR_MAX = 255


class ProfileEditForm(FlaskForm):
    """Edit the current user's profile (username, bio, avatar URL).

    Username uniqueness is checked at the route level because we need
    access to the database session and the current user's id.
    """

    username = StringField(
        "Username",
        filters=[lambda v: v.strip() if isinstance(v, str) else v],
        validators=[
            DataRequired(message="Username is required."),
            Length(
                min=3,
                max=64,
                message="Username must be between 3 and 64 characters.",
            ),
        ],
    )
    bio = TextAreaField(
        "Bio",
        filters=[lambda v: v.strip() if isinstance(v, str) else v],
        validators=[
            Optional(),
            Length(
                max=PROFILE_BIO_MAX,
                message=f"Bio must be {PROFILE_BIO_MAX} characters or fewer.",
            ),
        ],
    )
    avatar_path = StringField(
        "Avatar URL",
        filters=[lambda v: v.strip() if isinstance(v, str) else v],
        validators=[
            Optional(),
            Length(
                max=PROFILE_AVATAR_MAX,
                message="Avatar URL is too long.",
            ),
        ],
    )
    submit = SubmitField("Save changes")
