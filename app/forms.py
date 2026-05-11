"""WTForms definitions for the Movie Star app.

Each module owner should add their own form classes to this file (or to a
sub-package later if it grows too large). Forms here are server-side
schemas: they validate inputs, render CSRF tokens, and integrate with the
Flask request lifecycle.

Currently contains:
    - LoginForm     (Module A - Auth)
    - SignupForm    (Module A - Auth)
    - SearchForm    (Module B - Movies + Search)
"""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
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
