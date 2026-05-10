"""WTForms definitions for the Movie Star app.

Each module owner should add their own form classes to this file (or to a
sub-package later if it grows too large). Forms here are server-side
schemas: they validate inputs, render CSRF tokens, and integrate with the
Flask request lifecycle.

Currently contains:
    - SearchForm  (Module B - Movies + Search)
"""
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import Length, NumberRange, Optional


# Min-rating dropdown values shown on the search page.
# Stored as plain strings so the template can mark the active option easily.
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
