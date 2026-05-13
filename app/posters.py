"""Fetch real movie poster URLs from OMDb and update existing movies.

Usage:
    1. Get a free OMDb API key from https://www.omdbapi.com/apikey.aspx
       (pick the FREE tier — no credit card, key arrives by email instantly)
    2. Export it in your terminal:
           export OMDB_KEY=your_key_here
    3. Run:
           flask fetch-posters

The command iterates over every Movie row in the database, asks OMDb
"what's the poster URL for <title> (<year>)?", and updates the
`poster_path` column with the real URL.

OMDb returns Amazon-CDN URLs like:
    https://m.media-amazon.com/images/M/MV5BMjAxMzY3....jpg

These work directly in <img src=...> tags and load fast.

Free tier limit: 1000 requests/day. We have 25 movies, so plenty of
headroom even if you re-run.
"""
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

import click

from app import app, db
from app.models import Movie


def _fetch_poster_from_omdb(title: str, year: int, api_key: str) -> str | None:
    """Ask OMDb for a movie poster URL. Returns None if not found."""
    params = urlencode({"t": title, "y": year, "apikey": api_key})
    url = f"https://www.omdbapi.com/?{params}"

    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError, json.JSONDecodeError) as e:
        click.echo(f"  ! Network/parse error for {title}: {e}", err=True)
        return None

    if data.get("Response") != "True":
        click.echo(f"  ! OMDb didn't find {title} ({year}): {data.get('Error')}", err=True)
        return None

    poster = data.get("Poster")
    if not poster or poster == "N/A":
        click.echo(f"  ! No poster available for {title}", err=True)
        return None

    return poster


@app.cli.command("fetch-posters")
def fetch_posters():
    """Update Movie.poster_path with real URLs fetched from OMDb."""
    api_key = os.environ.get("OMDB_KEY")
    if not api_key:
        click.echo(
            "❌  OMDB_KEY environment variable not set.\n"
            "    Get a free key at https://www.omdbapi.com/apikey.aspx\n"
            "    Then: export OMDB_KEY=your_key_here",
            err=True,
        )
        return

    movies = Movie.query.order_by(Movie.title).all()
    if not movies:
        click.echo("No movies in the database. Run `flask seed-db` first.")
        return

    click.echo(f"Fetching posters for {len(movies)} movies...")
    click.echo("")

    updated = 0
    skipped = 0
    for m in movies:
        click.echo(f"  • {m.title} ({m.release_year})... ", nl=False)
        poster = _fetch_poster_from_omdb(m.title, m.release_year, api_key)
        if poster:
            m.poster_path = poster
            updated += 1
            click.echo("✓")
        else:
            skipped += 1
            click.echo("skipped")

    db.session.commit()

    click.echo("")
    click.echo(f"Done. Updated {updated}, skipped {skipped}.")
