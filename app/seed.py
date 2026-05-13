"""Seed the database with sample data for development and testing.

Usage:
    flask seed-db

This wipes ALL data from the seed-affected tables and reseeds. Don't run
on a database you've put real or hand-curated data into — anything not
in this file will be lost.

The seed is deliberately small (~25 movies, 6 users, ~40 reviews) so the
app feels populated without becoming unwieldy. A handful of edge cases
are seeded on purpose:
    - one user with no activity at all (ghost_user)
    - one user with an empty watchlist (maya_patel)
    - several movies with zero reviews (to exercise empty-state UI)
    - reviews ranging from one-line zingers to paragraph-length
    - threaded comment replies (exercises the self-FK)
"""
from datetime import date, datetime, timedelta
from urllib.parse import quote

import click

from app import app, db
from app.models import (
    Follow,
    Genre,
    Movie,
    Review,
    ReviewComment,
    ReviewLike,
    User,
    WatchlistItem,
    movie_genres,
)


# ─── Helpers ──────────────────────────────────────────────────────────


def _ago(days: int) -> datetime:
    """Return a UTC timestamp `days` days before now."""
    return datetime.utcnow() - timedelta(days=days)


def _poster(title: str) -> str:
    """Placeholder poster URL. Swap to real TMDb URLs in a future polish PR."""
    return f"https://placehold.co/500x750/1a1a2e/e0e0ff?text={quote(title)}"


# ─── Static data ──────────────────────────────────────────────────────


GENRE_NAMES = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Drama",
    "Horror",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
]


USERS = [
    {
        "username": "alex_chen",
        "email": "alex@example.com",
        "bio": "Movie nerd since 2003. Big on sci-fi, can't stand musicals (sorry).",
        "joined_days_ago": 365,
    },
    {
        "username": "sarah_kim",
        "email": "sarah@example.com",
        "bio": "Indie films and slow cinema. Usually behind on the blockbusters.",
        "joined_days_ago": 280,
    },
    {
        "username": "filmcritic99",
        "email": "film@example.com",
        "bio": "I have opinions about everything. You will not change my mind about The Tree of Life.",
        "joined_days_ago": 500,
    },
    {
        "username": "jordan_lee",
        "email": "jordan@example.com",
        "bio": "Horror obsessive. The scarier the better.",
        "joined_days_ago": 180,
    },
    {
        "username": "maya_patel",
        "email": "maya@example.com",
        "bio": "Just here to find something good to watch tonight.",
        "joined_days_ago": 14,
    },
    {
        # Edge case: empty profile, no activity anywhere.
        "username": "ghost_user",
        "email": "ghost@example.com",
        "bio": None,
        "joined_days_ago": 30,
    },
]


MOVIES = [
    {
        "title": "Inception",
        "release_year": 2010,
        "release_date": date(2010, 7, 16),
        "runtime_minutes": 148,
        "age_rating": "PG-13",
        "synopsis": "Dom Cobb extracts secrets from people's dreams for hire, but a final job offers him a chance to return home — if he can plant an idea instead of stealing one.",
        "director_name": "Christopher Nolan",
        "cast_text": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page, Tom Hardy, Marion Cotillard",
        "language": "en",
        "country": "US",
        "tmdb_id": 27205,
        "genres": ["Sci-Fi", "Action", "Thriller"],
    },
    {
        "title": "The Shawshank Redemption",
        "release_year": 1994,
        "release_date": date(1994, 9, 23),
        "runtime_minutes": 142,
        "age_rating": "R",
        "synopsis": "Banker Andy Dufresne is sentenced to life at Shawshank prison for a murder he didn't commit, where he forms an unexpected friendship and quietly plots his survival.",
        "director_name": "Frank Darabont",
        "cast_text": "Tim Robbins, Morgan Freeman, Bob Gunton, William Sadler",
        "language": "en",
        "country": "US",
        "tmdb_id": 278,
        "genres": ["Drama", "Crime"],
    },
    {
        "title": "Parasite",
        "release_year": 2019,
        "release_date": date(2019, 5, 30),
        "runtime_minutes": 132,
        "age_rating": "R",
        "synopsis": "A poor family schemes their way into the household of a wealthy clan, until a hidden secret threatens to unravel their entire arrangement.",
        "director_name": "Bong Joon-ho",
        "cast_text": "Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong, Choi Woo-shik, Park So-dam",
        "language": "ko",
        "country": "KR",
        "tmdb_id": 496243,
        "genres": ["Drama", "Thriller"],
    },
    {
        "title": "Spirited Away",
        "release_year": 2001,
        "release_date": date(2001, 7, 20),
        "runtime_minutes": 125,
        "age_rating": "PG",
        "synopsis": "Ten-year-old Chihiro stumbles into a hidden world of spirits and gods after her parents are transformed into pigs, and must work in a magical bathhouse to save them.",
        "director_name": "Hayao Miyazaki",
        "cast_text": "Rumi Hiiragi, Miyu Irino, Mari Natsuki, Takeshi Naito",
        "language": "ja",
        "country": "JP",
        "tmdb_id": 129,
        "genres": ["Animation", "Adventure"],
    },
    {
        "title": "Mad Max: Fury Road",
        "release_year": 2015,
        "release_date": date(2015, 5, 15),
        "runtime_minutes": 120,
        "age_rating": "R",
        "synopsis": "In a post-apocalyptic wasteland, a drifter named Max teams up with a renegade warrior to escape a tyrant ruler across an unforgiving desert.",
        "director_name": "George Miller",
        "cast_text": "Tom Hardy, Charlize Theron, Nicholas Hoult, Hugh Keays-Byrne",
        "language": "en",
        "country": "AU",
        "tmdb_id": 76341,
        "genres": ["Action", "Adventure"],
    },
    {
        "title": "The Dark Knight",
        "release_year": 2008,
        "release_date": date(2008, 7, 18),
        "runtime_minutes": 152,
        "age_rating": "PG-13",
        "synopsis": "Batman faces his greatest psychological test when a chaotic criminal mastermind known as the Joker descends on Gotham City.",
        "director_name": "Christopher Nolan",
        "cast_text": "Christian Bale, Heath Ledger, Aaron Eckhart, Maggie Gyllenhaal, Gary Oldman",
        "language": "en",
        "country": "US",
        "tmdb_id": 155,
        "genres": ["Action", "Crime", "Drama"],
    },
    {
        "title": "Get Out",
        "release_year": 2017,
        "release_date": date(2017, 2, 24),
        "runtime_minutes": 104,
        "age_rating": "R",
        "synopsis": "Chris visits his white girlfriend's family for the weekend and slowly realises something is deeply wrong with their picture-perfect community.",
        "director_name": "Jordan Peele",
        "cast_text": "Daniel Kaluuya, Allison Williams, Bradley Whitford, Catherine Keener",
        "language": "en",
        "country": "US",
        "tmdb_id": 419430,
        "genres": ["Horror", "Mystery", "Thriller"],
    },
    {
        "title": "La La Land",
        "release_year": 2016,
        "release_date": date(2016, 12, 9),
        "runtime_minutes": 128,
        "age_rating": "PG-13",
        "synopsis": "An aspiring actress and a struggling jazz musician meet in Los Angeles and fall in love while chasing dreams that pull them in opposite directions.",
        "director_name": "Damien Chazelle",
        "cast_text": "Ryan Gosling, Emma Stone, John Legend, Rosemarie DeWitt",
        "language": "en",
        "country": "US",
        "tmdb_id": 313369,
        "genres": ["Romance", "Drama", "Comedy"],
    },
    {
        "title": "Spider-Man: Into the Spider-Verse",
        "release_year": 2018,
        "release_date": date(2018, 12, 14),
        "runtime_minutes": 117,
        "age_rating": "PG",
        "synopsis": "Brooklyn teenager Miles Morales becomes Spider-Man, then meets a half-dozen other Spider-People from across the multiverse.",
        "director_name": "Bob Persichetti, Peter Ramsey, Rodney Rothman",
        "cast_text": "Shameik Moore, Jake Johnson, Hailee Steinfeld, Mahershala Ali",
        "language": "en",
        "country": "US",
        "tmdb_id": 324857,
        "genres": ["Animation", "Action", "Adventure"],
    },
    {
        "title": "The Grand Budapest Hotel",
        "release_year": 2014,
        "release_date": date(2014, 3, 7),
        "runtime_minutes": 99,
        "age_rating": "R",
        "synopsis": "A legendary concierge at a famed European hotel is framed for murder, and his loyal lobby boy helps him fight to clear his name.",
        "director_name": "Wes Anderson",
        "cast_text": "Ralph Fiennes, Tony Revolori, Saoirse Ronan, Adrien Brody, Willem Dafoe",
        "language": "en",
        "country": "US",
        "tmdb_id": 120467,
        "genres": ["Comedy", "Drama"],
    },
    {
        "title": "Interstellar",
        "release_year": 2014,
        "release_date": date(2014, 11, 7),
        "runtime_minutes": 169,
        "age_rating": "PG-13",
        "synopsis": "When Earth becomes uninhabitable, a former pilot leads a mission through a wormhole in search of a new home for humanity.",
        "director_name": "Christopher Nolan",
        "cast_text": "Matthew McConaughey, Anne Hathaway, Jessica Chastain, Michael Caine",
        "language": "en",
        "country": "US",
        "tmdb_id": 157336,
        "genres": ["Sci-Fi", "Adventure", "Drama"],
    },
    {
        "title": "Knives Out",
        "release_year": 2019,
        "release_date": date(2019, 11, 27),
        "runtime_minutes": 130,
        "age_rating": "PG-13",
        "synopsis": "A renowned mystery novelist dies under suspicious circumstances, and a peculiar detective is hired to untangle the secrets of his eccentric family.",
        "director_name": "Rian Johnson",
        "cast_text": "Daniel Craig, Chris Evans, Ana de Armas, Jamie Lee Curtis, Toni Collette",
        "language": "en",
        "country": "US",
        "tmdb_id": 546554,
        "genres": ["Mystery", "Comedy", "Crime"],
    },
    {
        "title": "Hereditary",
        "release_year": 2018,
        "release_date": date(2018, 6, 8),
        "runtime_minutes": 127,
        "age_rating": "R",
        "synopsis": "After a family matriarch passes away, her surviving relatives begin to uncover disturbing truths about their bloodline.",
        "director_name": "Ari Aster",
        "cast_text": "Toni Collette, Alex Wolff, Milly Shapiro, Gabriel Byrne",
        "language": "en",
        "country": "US",
        "tmdb_id": 493922,
        "genres": ["Horror", "Drama", "Mystery"],
    },
    {
        "title": "Moonlight",
        "release_year": 2016,
        "release_date": date(2016, 10, 21),
        "runtime_minutes": 111,
        "age_rating": "R",
        "synopsis": "A young Black man growing up in Miami navigates love, identity, and self-discovery across three pivotal chapters of his life.",
        "director_name": "Barry Jenkins",
        "cast_text": "Mahershala Ali, Naomie Harris, Trevante Rhodes, André Holland",
        "language": "en",
        "country": "US",
        "tmdb_id": 376867,
        "genres": ["Drama"],
    },
    {
        "title": "Dune",
        "release_year": 2021,
        "release_date": date(2021, 10, 22),
        "runtime_minutes": 155,
        "age_rating": "PG-13",
        "synopsis": "On a desert planet rich with the universe's most valuable resource, a young noble must accept his destiny as his family is betrayed by rival houses.",
        "director_name": "Denis Villeneuve",
        "cast_text": "Timothée Chalamet, Rebecca Ferguson, Oscar Isaac, Zendaya, Jason Momoa",
        "language": "en",
        "country": "US",
        "tmdb_id": 438631,
        "genres": ["Sci-Fi", "Adventure"],
    },
    {
        "title": "The Lord of the Rings: The Fellowship of the Ring",
        "release_year": 2001,
        "release_date": date(2001, 12, 19),
        "runtime_minutes": 178,
        "age_rating": "PG-13",
        "synopsis": "A young hobbit inherits a powerful ring and joins a fellowship on a perilous journey to destroy it before it falls into the wrong hands.",
        "director_name": "Peter Jackson",
        "cast_text": "Elijah Wood, Ian McKellen, Viggo Mortensen, Sean Astin, Cate Blanchett",
        "language": "en",
        "country": "NZ",
        "tmdb_id": 120,
        "genres": ["Adventure", "Drama"],
    },
    {
        "title": "Whiplash",
        "release_year": 2014,
        "release_date": date(2014, 10, 10),
        "runtime_minutes": 106,
        "age_rating": "R",
        "synopsis": "A driven young drummer enrolls at an elite music conservatory, where his teacher's brutal methods push him to the brink.",
        "director_name": "Damien Chazelle",
        "cast_text": "Miles Teller, J.K. Simmons, Paul Reiser, Melissa Benoist",
        "language": "en",
        "country": "US",
        "tmdb_id": 244786,
        "genres": ["Drama"],
    },
    {
        "title": "John Wick",
        "release_year": 2014,
        "release_date": date(2014, 10, 24),
        "runtime_minutes": 101,
        "age_rating": "R",
        "synopsis": "A retired hitman returns to the underworld to seek revenge after a senseless crime takes everything he had left.",
        "director_name": "Chad Stahelski",
        "cast_text": "Keanu Reeves, Michael Nyqvist, Alfie Allen, Willem Dafoe",
        "language": "en",
        "country": "US",
        "tmdb_id": 245891,
        "genres": ["Action", "Thriller"],
    },
    {
        "title": "Lady Bird",
        "release_year": 2017,
        "release_date": date(2017, 11, 3),
        "runtime_minutes": 94,
        "age_rating": "R",
        "synopsis": "A headstrong high school senior in Sacramento clashes with her mother as she dreams of life beyond their hometown.",
        "director_name": "Greta Gerwig",
        "cast_text": "Saoirse Ronan, Laurie Metcalf, Tracy Letts, Lucas Hedges",
        "language": "en",
        "country": "US",
        "tmdb_id": 391713,
        "genres": ["Drama", "Comedy"],
    },
    {
        "title": "Blade Runner 2049",
        "release_year": 2017,
        "release_date": date(2017, 10, 6),
        "runtime_minutes": 164,
        "age_rating": "R",
        "synopsis": "Thirty years after the original, a new blade runner uncovers a long-buried secret that could plunge society into chaos.",
        "director_name": "Denis Villeneuve",
        "cast_text": "Ryan Gosling, Harrison Ford, Ana de Armas, Sylvia Hoeks, Jared Leto",
        "language": "en",
        "country": "US",
        "tmdb_id": 335984,
        "genres": ["Sci-Fi", "Drama", "Mystery"],
    },
    {
        "title": "Toy Story",
        "release_year": 1995,
        "release_date": date(1995, 11, 22),
        "runtime_minutes": 81,
        "age_rating": "G",
        "synopsis": "When a new spaceman action figure threatens his place as the favourite toy, a cowboy doll's jealousy spirals into an unexpected adventure.",
        "director_name": "John Lasseter",
        "cast_text": "Tom Hanks, Tim Allen, Don Rickles, Jim Varney, Wallace Shawn",
        "language": "en",
        "country": "US",
        "tmdb_id": 862,
        "genres": ["Animation", "Adventure", "Comedy"],
    },
    {
        "title": "No Country for Old Men",
        "release_year": 2007,
        "release_date": date(2007, 11, 9),
        "runtime_minutes": 122,
        "age_rating": "R",
        "synopsis": "A Texas hunter stumbles upon the aftermath of a drug deal gone wrong and finds two million dollars, drawing the attention of a relentless killer.",
        "director_name": "Joel Coen, Ethan Coen",
        "cast_text": "Tommy Lee Jones, Javier Bardem, Josh Brolin, Woody Harrelson",
        "language": "en",
        "country": "US",
        "tmdb_id": 6977,
        "genres": ["Crime", "Drama", "Thriller"],
    },
    {
        "title": "Bridesmaids",
        "release_year": 2011,
        "release_date": date(2011, 5, 13),
        "runtime_minutes": 125,
        "age_rating": "R",
        "synopsis": "An out-of-luck single woman is asked to be maid of honour at her best friend's wedding, with disastrous consequences.",
        "director_name": "Paul Feig",
        "cast_text": "Kristen Wiig, Maya Rudolph, Rose Byrne, Melissa McCarthy",
        "language": "en",
        "country": "US",
        "tmdb_id": 55721,
        "genres": ["Comedy", "Romance"],
    },
    {
        "title": "The Babadook",
        "release_year": 2014,
        "release_date": date(2014, 5, 22),
        "runtime_minutes": 94,
        "age_rating": "R",
        "synopsis": "A widowed mother and her troubled son are haunted by a sinister presence from a children's book that mysteriously appears in their home.",
        "director_name": "Jennifer Kent",
        "cast_text": "Essie Davis, Noah Wiseman, Daniel Henshall, Hayley McElhinney",
        "language": "en",
        "country": "AU",
        "tmdb_id": 242224,
        "genres": ["Horror", "Drama"],
    },
    {
        "title": "Everything Everywhere All at Once",
        "release_year": 2022,
        "release_date": date(2022, 3, 25),
        "runtime_minutes": 139,
        "age_rating": "R",
        "synopsis": "An overworked Chinese-American laundromat owner is unexpectedly thrust into saving the multiverse by tapping into versions of herself across parallel lives.",
        "director_name": "Daniel Kwan, Daniel Scheinert",
        "cast_text": "Michelle Yeoh, Ke Huy Quan, Stephanie Hsu, Jamie Lee Curtis",
        "language": "en",
        "country": "US",
        "tmdb_id": 545611,
        "genres": ["Sci-Fi", "Comedy", "Action"],
    },

    # ─── Pre-1980s classics ────────────────────────────
    {
        "title": "Citizen Kane",
        "release_year": 1941,
        "release_date": date(1941, 9, 5),
        "runtime_minutes": 119,
        "age_rating": "PG",
        "synopsis": "A reporter investigates the dying words of a publishing magnate and uncovers the fractured life behind the public legend.",
        "director_name": "Orson Welles",
        "cast_text": "Orson Welles, Joseph Cotten, Dorothy Comingore, Agnes Moorehead",
        "language": "en", "country": "US",
        "genres": ["Drama", "Mystery"],
    },
    {
        "title": "Casablanca",
        "release_year": 1942,
        "release_date": date(1942, 11, 26),
        "runtime_minutes": 102,
        "age_rating": "PG",
        "synopsis": "A cynical American club owner in wartime Morocco is forced to choose between love and resistance when his former lover walks back into his life.",
        "director_name": "Michael Curtiz",
        "cast_text": "Humphrey Bogart, Ingrid Bergman, Paul Henreid, Claude Rains",
        "language": "en", "country": "US",
        "genres": ["Drama", "Romance"],
    },
    {
        "title": "2001: A Space Odyssey",
        "release_year": 1968,
        "release_date": date(1968, 4, 2),
        "runtime_minutes": 149,
        "age_rating": "G",
        "synopsis": "From the dawn of humanity to a voyage past Jupiter, an enigmatic black monolith marks the strange evolutionary path of our species.",
        "director_name": "Stanley Kubrick",
        "cast_text": "Keir Dullea, Gary Lockwood, William Sylvester, Douglas Rain",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Adventure"],
    },
    {
        "title": "The Godfather",
        "release_year": 1972,
        "release_date": date(1972, 3, 24),
        "runtime_minutes": 175,
        "age_rating": "R",
        "synopsis": "The reluctant youngest son of an aging Mafia patriarch is drawn into the family business after an attempt on his father's life.",
        "director_name": "Francis Ford Coppola",
        "cast_text": "Marlon Brando, Al Pacino, James Caan, Robert Duvall, Diane Keaton",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama"],
    },
    {
        "title": "Jaws",
        "release_year": 1975,
        "release_date": date(1975, 6, 20),
        "runtime_minutes": 124,
        "age_rating": "PG",
        "synopsis": "A small seaside town's sheriff, a marine biologist, and a grizzled shark hunter set out to stop a great white terrorising their beaches.",
        "director_name": "Steven Spielberg",
        "cast_text": "Roy Scheider, Robert Shaw, Richard Dreyfuss, Lorraine Gary",
        "language": "en", "country": "US",
        "genres": ["Adventure", "Thriller"],
    },
    {
        "title": "Taxi Driver",
        "release_year": 1976,
        "release_date": date(1976, 2, 8),
        "runtime_minutes": 114,
        "age_rating": "R",
        "synopsis": "An insomniac Vietnam veteran working as a New York cab driver spirals into a violent vigilante mission to save a young runaway.",
        "director_name": "Martin Scorsese",
        "cast_text": "Robert De Niro, Jodie Foster, Cybill Shepherd, Harvey Keitel",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama"],
    },
    {
        "title": "Star Wars: A New Hope",
        "release_year": 1977,
        "release_date": date(1977, 5, 25),
        "runtime_minutes": 121,
        "age_rating": "PG",
        "synopsis": "A farm boy joins a band of rebels and a wise mentor to rescue a captured princess from an evil galactic empire.",
        "director_name": "George Lucas",
        "cast_text": "Mark Hamill, Harrison Ford, Carrie Fisher, Alec Guinness, Peter Cushing",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Adventure", "Action"],
    },
    {
        "title": "Alien",
        "release_year": 1979,
        "release_date": date(1979, 5, 25),
        "runtime_minutes": 117,
        "age_rating": "R",
        "synopsis": "The crew of a commercial space tug answers a distress call and brings something deadly back aboard their ship.",
        "director_name": "Ridley Scott",
        "cast_text": "Sigourney Weaver, Tom Skerritt, John Hurt, Ian Holm, Yaphet Kotto",
        "language": "en", "country": "US",
        "genres": ["Horror", "Sci-Fi"],
    },
    {
        "title": "The Shining",
        "release_year": 1980,
        "release_date": date(1980, 5, 23),
        "runtime_minutes": 146,
        "age_rating": "R",
        "synopsis": "An aspiring writer takes a winter caretaker job at a remote mountain hotel where supernatural forces slowly unravel his sanity.",
        "director_name": "Stanley Kubrick",
        "cast_text": "Jack Nicholson, Shelley Duvall, Danny Lloyd, Scatman Crothers",
        "language": "en", "country": "US",
        "genres": ["Horror", "Drama"],
    },
    {
        "title": "Raiders of the Lost Ark",
        "release_year": 1981,
        "release_date": date(1981, 6, 12),
        "runtime_minutes": 115,
        "age_rating": "PG",
        "synopsis": "An archaeology professor races Nazi agents across the globe to recover a biblical artifact of unimaginable power.",
        "director_name": "Steven Spielberg",
        "cast_text": "Harrison Ford, Karen Allen, Paul Freeman, John Rhys-Davies",
        "language": "en", "country": "US",
        "genres": ["Action", "Adventure"],
    },
    {
        "title": "Blade Runner",
        "release_year": 1982,
        "release_date": date(1982, 6, 25),
        "runtime_minutes": 117,
        "age_rating": "R",
        "synopsis": "A burnt-out detective in a future Los Angeles hunts a group of escaped bioengineered replicants seeking more life.",
        "director_name": "Ridley Scott",
        "cast_text": "Harrison Ford, Rutger Hauer, Sean Young, Edward James Olmos, Daryl Hannah",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Drama", "Mystery"],
    },
    {
        "title": "Back to the Future",
        "release_year": 1985,
        "release_date": date(1985, 7, 3),
        "runtime_minutes": 116,
        "age_rating": "PG",
        "synopsis": "A teenager is accidentally sent thirty years into the past in a time-travelling DeLorean and must ensure his parents fall in love.",
        "director_name": "Robert Zemeckis",
        "cast_text": "Michael J. Fox, Christopher Lloyd, Lea Thompson, Crispin Glover",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Adventure", "Comedy"],
    },

    # ─── 1990s ────────────────────────────────────────
    {
        "title": "Goodfellas",
        "release_year": 1990,
        "release_date": date(1990, 9, 19),
        "runtime_minutes": 145,
        "age_rating": "R",
        "synopsis": "Across three decades, a young man rises through the ranks of a New York crime family before everything begins to unravel.",
        "director_name": "Martin Scorsese",
        "cast_text": "Robert De Niro, Ray Liotta, Joe Pesci, Lorraine Bracco, Paul Sorvino",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama"],
    },
    {
        "title": "The Silence of the Lambs",
        "release_year": 1991,
        "release_date": date(1991, 2, 14),
        "runtime_minutes": 118,
        "age_rating": "R",
        "synopsis": "A young FBI trainee seeks the help of an imprisoned cannibal psychiatrist to catch another serial killer at large.",
        "director_name": "Jonathan Demme",
        "cast_text": "Jodie Foster, Anthony Hopkins, Scott Glenn, Ted Levine",
        "language": "en", "country": "US",
        "genres": ["Thriller", "Crime", "Horror"],
    },
    {
        "title": "Terminator 2: Judgment Day",
        "release_year": 1991,
        "release_date": date(1991, 7, 3),
        "runtime_minutes": 137,
        "age_rating": "R",
        "synopsis": "A reprogrammed cyborg returns from the future to protect the boy who will lead humanity's resistance from an even deadlier machine.",
        "director_name": "James Cameron",
        "cast_text": "Arnold Schwarzenegger, Linda Hamilton, Edward Furlong, Robert Patrick",
        "language": "en", "country": "US",
        "genres": ["Action", "Sci-Fi"],
    },
    {
        "title": "Jurassic Park",
        "release_year": 1993,
        "release_date": date(1993, 6, 11),
        "runtime_minutes": 127,
        "age_rating": "PG-13",
        "synopsis": "A billionaire opens a tropical island theme park populated with cloned dinosaurs, with predictable but spectacular consequences.",
        "director_name": "Steven Spielberg",
        "cast_text": "Sam Neill, Laura Dern, Jeff Goldblum, Richard Attenborough",
        "language": "en", "country": "US",
        "genres": ["Adventure", "Sci-Fi", "Action"],
    },
    {
        "title": "Schindler's List",
        "release_year": 1993,
        "release_date": date(1993, 12, 15),
        "runtime_minutes": 195,
        "age_rating": "R",
        "synopsis": "A pragmatic German businessman gradually risks his fortune and life to save his Jewish workforce from the Holocaust.",
        "director_name": "Steven Spielberg",
        "cast_text": "Liam Neeson, Ralph Fiennes, Ben Kingsley, Caroline Goodall",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Pulp Fiction",
        "release_year": 1994,
        "release_date": date(1994, 10, 14),
        "runtime_minutes": 154,
        "age_rating": "R",
        "synopsis": "Hitmen, a boxer, a mob boss's wife, and two diner robbers weave through interconnected stories in 1990s Los Angeles.",
        "director_name": "Quentin Tarantino",
        "cast_text": "John Travolta, Samuel L. Jackson, Uma Thurman, Bruce Willis, Ving Rhames",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama"],
    },
    {
        "title": "Forrest Gump",
        "release_year": 1994,
        "release_date": date(1994, 7, 6),
        "runtime_minutes": 142,
        "age_rating": "PG-13",
        "synopsis": "A simple-hearted Alabama man with a low IQ stumbles through several of the defining moments of 20th-century American history.",
        "director_name": "Robert Zemeckis",
        "cast_text": "Tom Hanks, Robin Wright, Gary Sinise, Mykelti Williamson, Sally Field",
        "language": "en", "country": "US",
        "genres": ["Drama", "Romance", "Comedy"],
    },
    {
        "title": "The Lion King",
        "release_year": 1994,
        "release_date": date(1994, 6, 15),
        "runtime_minutes": 88,
        "age_rating": "G",
        "synopsis": "A young lion prince flees his kingdom in shame after his father's death and must one day return to claim his rightful throne.",
        "director_name": "Roger Allers, Rob Minkoff",
        "cast_text": "Matthew Broderick, Jeremy Irons, James Earl Jones, Nathan Lane",
        "language": "en", "country": "US",
        "genres": ["Animation", "Adventure", "Drama"],
    },
    {
        "title": "Se7en",
        "release_year": 1995,
        "release_date": date(1995, 9, 22),
        "runtime_minutes": 127,
        "age_rating": "R",
        "synopsis": "Two detectives — a retiring veteran and his eager replacement — hunt a serial killer modelling his murders on the seven deadly sins.",
        "director_name": "David Fincher",
        "cast_text": "Brad Pitt, Morgan Freeman, Gwyneth Paltrow, Kevin Spacey",
        "language": "en", "country": "US",
        "genres": ["Crime", "Mystery", "Thriller"],
    },
    {
        "title": "Trainspotting",
        "release_year": 1996,
        "release_date": date(1996, 2, 23),
        "runtime_minutes": 93,
        "age_rating": "R",
        "synopsis": "A group of heroin addicts in Edinburgh stumble between bleak humour and disaster as one of them tries to clean up.",
        "director_name": "Danny Boyle",
        "cast_text": "Ewan McGregor, Ewen Bremner, Jonny Lee Miller, Kelly Macdonald, Robert Carlyle",
        "language": "en", "country": "GB",
        "genres": ["Drama", "Crime"],
    },
    {
        "title": "Titanic",
        "release_year": 1997,
        "release_date": date(1997, 12, 19),
        "runtime_minutes": 195,
        "age_rating": "PG-13",
        "synopsis": "A penniless artist and a young first-class passenger fall in love on the doomed maiden voyage of the famed ocean liner.",
        "director_name": "James Cameron",
        "cast_text": "Leonardo DiCaprio, Kate Winslet, Billy Zane, Kathy Bates, Bill Paxton",
        "language": "en", "country": "US",
        "genres": ["Romance", "Drama"],
    },
    {
        "title": "Good Will Hunting",
        "release_year": 1997,
        "release_date": date(1997, 12, 5),
        "runtime_minutes": 126,
        "age_rating": "R",
        "synopsis": "A janitor at MIT with a gift for mathematics is offered a way out of his dead-end Boston life through therapy and an unconventional mentor.",
        "director_name": "Gus Van Sant",
        "cast_text": "Matt Damon, Robin Williams, Ben Affleck, Minnie Driver, Stellan Skarsgård",
        "language": "en", "country": "US",
        "genres": ["Drama", "Romance"],
    },
    {
        "title": "The Big Lebowski",
        "release_year": 1998,
        "release_date": date(1998, 3, 6),
        "runtime_minutes": 117,
        "age_rating": "R",
        "synopsis": "A laid-back Los Angeles slacker mistaken for a millionaire of the same name is dragged into a kidnapping caper involving a rug, nihilists, and bowling.",
        "director_name": "Joel Coen, Ethan Coen",
        "cast_text": "Jeff Bridges, John Goodman, Julianne Moore, Steve Buscemi, John Turturro",
        "language": "en", "country": "US",
        "genres": ["Comedy", "Crime"],
    },
    {
        "title": "The Matrix",
        "release_year": 1999,
        "release_date": date(1999, 3, 31),
        "runtime_minutes": 136,
        "age_rating": "R",
        "synopsis": "A disillusioned hacker discovers that reality as he knows it is a simulation and joins a rebellion against the machines running it.",
        "director_name": "Lana Wachowski, Lilly Wachowski",
        "cast_text": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss, Hugo Weaving",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Action"],
    },
    {
        "title": "Fight Club",
        "release_year": 1999,
        "release_date": date(1999, 10, 15),
        "runtime_minutes": 139,
        "age_rating": "R",
        "synopsis": "An insomniac office worker forms an underground fighting club with a charismatic soap salesman that grows into something much more dangerous.",
        "director_name": "David Fincher",
        "cast_text": "Brad Pitt, Edward Norton, Helena Bonham Carter, Meat Loaf",
        "language": "en", "country": "US",
        "genres": ["Drama", "Thriller"],
    },

    # ─── 2000s ────────────────────────────────────────
    {
        "title": "Memento",
        "release_year": 2000,
        "release_date": date(2000, 10, 11),
        "runtime_minutes": 113,
        "age_rating": "R",
        "synopsis": "A man with no short-term memory uses Polaroids and tattoos to hunt the person he believes murdered his wife.",
        "director_name": "Christopher Nolan",
        "cast_text": "Guy Pearce, Carrie-Anne Moss, Joe Pantoliano, Mark Boone Junior",
        "language": "en", "country": "US",
        "genres": ["Mystery", "Thriller", "Drama"],
    },
    {
        "title": "Crouching Tiger, Hidden Dragon",
        "release_year": 2000,
        "release_date": date(2000, 7, 7),
        "runtime_minutes": 120,
        "age_rating": "PG-13",
        "synopsis": "Two warriors search for a stolen sword and find their pasts catching up with them in the wuxia tradition of imperial China.",
        "director_name": "Ang Lee",
        "cast_text": "Chow Yun-fat, Michelle Yeoh, Zhang Ziyi, Chang Chen",
        "language": "zh", "country": "TW",
        "genres": ["Action", "Drama", "Romance"],
    },
    {
        "title": "Amélie",
        "release_year": 2001,
        "release_date": date(2001, 4, 25),
        "runtime_minutes": 122,
        "age_rating": "R",
        "synopsis": "A shy Parisian waitress decides to secretly orchestrate small acts of kindness for the people around her — and accidentally finds love.",
        "director_name": "Jean-Pierre Jeunet",
        "cast_text": "Audrey Tautou, Mathieu Kassovitz, Rufus, Lorella Cravotta",
        "language": "fr", "country": "FR",
        "genres": ["Comedy", "Romance", "Drama"],
    },
    {
        "title": "Mulholland Drive",
        "release_year": 2001,
        "release_date": date(2001, 10, 19),
        "runtime_minutes": 147,
        "age_rating": "R",
        "synopsis": "A bright-eyed aspiring actress arriving in Hollywood befriends an amnesiac woman, and reality itself begins to fold in on them.",
        "director_name": "David Lynch",
        "cast_text": "Naomi Watts, Laura Harring, Justin Theroux, Ann Miller",
        "language": "en", "country": "US",
        "genres": ["Mystery", "Drama", "Thriller"],
    },
    {
        "title": "Lost in Translation",
        "release_year": 2003,
        "release_date": date(2003, 9, 12),
        "runtime_minutes": 102,
        "age_rating": "R",
        "synopsis": "A faded American movie star and a young newlywed find unexpected companionship over a few jet-lagged days in Tokyo.",
        "director_name": "Sofia Coppola",
        "cast_text": "Bill Murray, Scarlett Johansson, Giovanni Ribisi, Anna Faris",
        "language": "en", "country": "US",
        "genres": ["Drama", "Romance", "Comedy"],
    },
    {
        "title": "Kill Bill: Vol. 1",
        "release_year": 2003,
        "release_date": date(2003, 10, 10),
        "runtime_minutes": 111,
        "age_rating": "R",
        "synopsis": "A former assassin awakens from a coma and sets out to take violent revenge against the squad that left her for dead.",
        "director_name": "Quentin Tarantino",
        "cast_text": "Uma Thurman, Lucy Liu, Vivica A. Fox, Daryl Hannah, David Carradine",
        "language": "en", "country": "US",
        "genres": ["Action", "Crime", "Thriller"],
    },
    {
        "title": "Eternal Sunshine of the Spotless Mind",
        "release_year": 2004,
        "release_date": date(2004, 3, 19),
        "runtime_minutes": 108,
        "age_rating": "R",
        "synopsis": "After a painful breakup, a man undergoes an experimental procedure to erase his ex-girlfriend from his memory — and changes his mind partway through.",
        "director_name": "Michel Gondry",
        "cast_text": "Jim Carrey, Kate Winslet, Kirsten Dunst, Mark Ruffalo, Elijah Wood",
        "language": "en", "country": "US",
        "genres": ["Romance", "Drama", "Sci-Fi"],
    },
    {
        "title": "The Departed",
        "release_year": 2006,
        "release_date": date(2006, 10, 6),
        "runtime_minutes": 151,
        "age_rating": "R",
        "synopsis": "A young cop infiltrates the Boston Irish mob while a mole within the police force feeds intel back the other way. Both men race to identify each other first.",
        "director_name": "Martin Scorsese",
        "cast_text": "Leonardo DiCaprio, Matt Damon, Jack Nicholson, Mark Wahlberg, Vera Farmiga",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama", "Thriller"],
    },
    {
        "title": "Hot Fuzz",
        "release_year": 2007,
        "release_date": date(2007, 2, 14),
        "runtime_minutes": 121,
        "age_rating": "R",
        "synopsis": "A by-the-book London supercop is exiled to a sleepy English village where a string of grisly 'accidents' suggests something deeply weird underneath the rose bushes.",
        "director_name": "Edgar Wright",
        "cast_text": "Simon Pegg, Nick Frost, Jim Broadbent, Timothy Dalton",
        "language": "en", "country": "GB",
        "genres": ["Comedy", "Action", "Mystery"],
    },
    {
        "title": "There Will Be Blood",
        "release_year": 2007,
        "release_date": date(2007, 12, 26),
        "runtime_minutes": 158,
        "age_rating": "R",
        "synopsis": "A ruthless turn-of-the-century oil prospector consolidates power across the California frontier while his soul corrodes into something terrible.",
        "director_name": "Paul Thomas Anderson",
        "cast_text": "Daniel Day-Lewis, Paul Dano, Ciarán Hinds, Dillon Freasier",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "WALL·E",
        "release_year": 2008,
        "release_date": date(2008, 6, 27),
        "runtime_minutes": 98,
        "age_rating": "G",
        "synopsis": "A lonely waste-collecting robot on an abandoned Earth meets a sleek probe and follows her into space, accidentally igniting humanity's redemption.",
        "director_name": "Andrew Stanton",
        "cast_text": "Ben Burtt, Elissa Knight, Jeff Garlin, Fred Willard, John Ratzenberger",
        "language": "en", "country": "US",
        "genres": ["Animation", "Adventure", "Sci-Fi"],
    },
    {
        "title": "In Bruges",
        "release_year": 2008,
        "release_date": date(2008, 2, 8),
        "runtime_minutes": 107,
        "age_rating": "R",
        "synopsis": "Two Irish hitmen lay low in a fairytale Belgian town after a job goes wrong, while their boss decides what to do about them.",
        "director_name": "Martin McDonagh",
        "cast_text": "Colin Farrell, Brendan Gleeson, Ralph Fiennes, Clémence Poésy",
        "language": "en", "country": "GB",
        "genres": ["Crime", "Drama", "Comedy"],
    },
    {
        "title": "Up",
        "release_year": 2009,
        "release_date": date(2009, 5, 29),
        "runtime_minutes": 96,
        "age_rating": "PG",
        "synopsis": "After his wife's death, an elderly widower ties thousands of balloons to his house and floats away to South America, with an accidental boy-scout passenger on board.",
        "director_name": "Pete Docter",
        "cast_text": "Edward Asner, Jordan Nagai, Christopher Plummer, Bob Peterson",
        "language": "en", "country": "US",
        "genres": ["Animation", "Adventure", "Comedy", "Drama"],
    },

    # ─── 2010s ────────────────────────────────────────
    {
        "title": "Black Swan",
        "release_year": 2010,
        "release_date": date(2010, 12, 3),
        "runtime_minutes": 108,
        "age_rating": "R",
        "synopsis": "A fragile ballerina cast as the lead in Swan Lake loses her grip on reality as she pursues the dark perfection the role demands.",
        "director_name": "Darren Aronofsky",
        "cast_text": "Natalie Portman, Mila Kunis, Vincent Cassel, Barbara Hershey, Winona Ryder",
        "language": "en", "country": "US",
        "genres": ["Drama", "Thriller", "Horror"],
    },
    {
        "title": "The Social Network",
        "release_year": 2010,
        "release_date": date(2010, 10, 1),
        "runtime_minutes": 120,
        "age_rating": "PG-13",
        "synopsis": "The dramatised origin of Facebook — a Harvard sophomore's idea spirals into a global empire and a tangle of lawsuits.",
        "director_name": "David Fincher",
        "cast_text": "Jesse Eisenberg, Andrew Garfield, Justin Timberlake, Armie Hammer, Rooney Mara",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Drive",
        "release_year": 2011,
        "release_date": date(2011, 9, 16),
        "runtime_minutes": 100,
        "age_rating": "R",
        "synopsis": "A Hollywood stunt driver who moonlights as a getaway driver protects his neighbour from a job gone catastrophically wrong.",
        "director_name": "Nicolas Winding Refn",
        "cast_text": "Ryan Gosling, Carey Mulligan, Bryan Cranston, Albert Brooks, Ron Perlman",
        "language": "en", "country": "US",
        "genres": ["Action", "Crime", "Drama"],
    },
    {
        "title": "The Cabin in the Woods",
        "release_year": 2012,
        "release_date": date(2012, 4, 13),
        "runtime_minutes": 95,
        "age_rating": "R",
        "synopsis": "Five college friends head to a remote cabin for a weekend trip, unaware that their entire ordeal is being orchestrated from beneath.",
        "director_name": "Drew Goddard",
        "cast_text": "Kristen Connolly, Chris Hemsworth, Anna Hutchison, Fran Kranz, Richard Jenkins",
        "language": "en", "country": "US",
        "genres": ["Horror", "Mystery", "Comedy"],
    },
    {
        "title": "Django Unchained",
        "release_year": 2012,
        "release_date": date(2012, 12, 25),
        "runtime_minutes": 165,
        "age_rating": "R",
        "synopsis": "A freed slave teams up with a German bounty hunter to rescue his wife from a charismatic, cruel Mississippi plantation owner.",
        "director_name": "Quentin Tarantino",
        "cast_text": "Jamie Foxx, Christoph Waltz, Leonardo DiCaprio, Kerry Washington, Samuel L. Jackson",
        "language": "en", "country": "US",
        "genres": ["Drama", "Action"],
    },
    {
        "title": "12 Years a Slave",
        "release_year": 2013,
        "release_date": date(2013, 10, 18),
        "runtime_minutes": 134,
        "age_rating": "R",
        "synopsis": "A free Black man in 1840s New York is kidnapped and sold into slavery in the deep South, where he endures more than a decade of captivity.",
        "director_name": "Steve McQueen",
        "cast_text": "Chiwetel Ejiofor, Michael Fassbender, Lupita Nyong'o, Benedict Cumberbatch",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Her",
        "release_year": 2013,
        "release_date": date(2013, 12, 18),
        "runtime_minutes": 126,
        "age_rating": "R",
        "synopsis": "A lonely letter-writer in a near-future Los Angeles falls in love with an artificially intelligent operating system who is also growing in her own direction.",
        "director_name": "Spike Jonze",
        "cast_text": "Joaquin Phoenix, Scarlett Johansson, Amy Adams, Rooney Mara",
        "language": "en", "country": "US",
        "genres": ["Romance", "Drama", "Sci-Fi"],
    },
    {
        "title": "Gravity",
        "release_year": 2013,
        "release_date": date(2013, 10, 4),
        "runtime_minutes": 91,
        "age_rating": "PG-13",
        "synopsis": "Two astronauts on a spacewalk are stranded in orbit when debris destroys their shuttle, and one has to claw her way home.",
        "director_name": "Alfonso Cuarón",
        "cast_text": "Sandra Bullock, George Clooney, Ed Harris",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Drama", "Thriller"],
    },
    {
        "title": "Boyhood",
        "release_year": 2014,
        "release_date": date(2014, 7, 11),
        "runtime_minutes": 165,
        "age_rating": "R",
        "synopsis": "Filmed over twelve years with the same cast, the story of a Texas boy growing up — divorce, school, first love, leaving home.",
        "director_name": "Richard Linklater",
        "cast_text": "Ellar Coltrane, Patricia Arquette, Ethan Hawke, Lorelei Linklater",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Birdman",
        "release_year": 2014,
        "release_date": date(2014, 10, 17),
        "runtime_minutes": 119,
        "age_rating": "R",
        "synopsis": "A washed-up superhero actor stakes everything on directing himself in a Broadway play, while his sanity audibly disintegrates backstage.",
        "director_name": "Alejandro González Iñárritu",
        "cast_text": "Michael Keaton, Edward Norton, Emma Stone, Naomi Watts, Zach Galifianakis",
        "language": "en", "country": "US",
        "genres": ["Drama", "Comedy"],
    },
    {
        "title": "The Witch",
        "release_year": 2015,
        "release_date": date(2015, 1, 27),
        "runtime_minutes": 92,
        "age_rating": "R",
        "synopsis": "A 17th-century Puritan family banished to the edge of the New England wilderness begins to suspect supernatural forces are pulling them apart.",
        "director_name": "Robert Eggers",
        "cast_text": "Anya Taylor-Joy, Ralph Ineson, Kate Dickie, Harvey Scrimshaw",
        "language": "en", "country": "US",
        "genres": ["Horror", "Drama", "Mystery"],
    },
    {
        "title": "Inside Out",
        "release_year": 2015,
        "release_date": date(2015, 6, 19),
        "runtime_minutes": 95,
        "age_rating": "PG",
        "synopsis": "An eleven-year-old girl's emotional life is portrayed as five anthropomorphic feelings in the control room of her mind.",
        "director_name": "Pete Docter",
        "cast_text": "Amy Poehler, Phyllis Smith, Bill Hader, Lewis Black, Mindy Kaling",
        "language": "en", "country": "US",
        "genres": ["Animation", "Comedy", "Drama"],
    },
    {
        "title": "The Revenant",
        "release_year": 2015,
        "release_date": date(2015, 12, 25),
        "runtime_minutes": 156,
        "age_rating": "R",
        "synopsis": "A frontier fur trapper survives a bear attack and his own companions' betrayal, then crawls hundreds of miles across the wilderness for revenge.",
        "director_name": "Alejandro González Iñárritu",
        "cast_text": "Leonardo DiCaprio, Tom Hardy, Domhnall Gleeson, Will Poulter",
        "language": "en", "country": "US",
        "genres": ["Adventure", "Drama"],
    },
    {
        "title": "Room",
        "release_year": 2015,
        "release_date": date(2015, 10, 16),
        "runtime_minutes": 117,
        "age_rating": "R",
        "synopsis": "A mother and her five-year-old son escape the small shed they've been imprisoned in for years and reckon with the strange wide world beyond.",
        "director_name": "Lenny Abrahamson",
        "cast_text": "Brie Larson, Jacob Tremblay, Joan Allen, Sean Bridgers, William H. Macy",
        "language": "en", "country": "IE",
        "genres": ["Drama", "Thriller"],
    },
    {
        "title": "Arrival",
        "release_year": 2016,
        "release_date": date(2016, 11, 11),
        "runtime_minutes": 116,
        "age_rating": "PG-13",
        "synopsis": "A linguist is recruited by the military to communicate with alien visitors and discovers that language reshapes time itself.",
        "director_name": "Denis Villeneuve",
        "cast_text": "Amy Adams, Jeremy Renner, Forest Whitaker, Michael Stuhlbarg",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Drama", "Mystery"],
    },
    {
        "title": "Manchester by the Sea",
        "release_year": 2016,
        "release_date": date(2016, 11, 18),
        "runtime_minutes": 137,
        "age_rating": "R",
        "synopsis": "A taciturn janitor returns to his hometown after his brother's death and finds he's been named guardian of his teenage nephew.",
        "director_name": "Kenneth Lonergan",
        "cast_text": "Casey Affleck, Michelle Williams, Lucas Hedges, Kyle Chandler",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Three Billboards Outside Ebbing, Missouri",
        "release_year": 2017,
        "release_date": date(2017, 11, 10),
        "runtime_minutes": 115,
        "age_rating": "R",
        "synopsis": "A grieving mother rents three roadside billboards to call out the local police's failure to solve her daughter's murder, and the small town implodes.",
        "director_name": "Martin McDonagh",
        "cast_text": "Frances McDormand, Sam Rockwell, Woody Harrelson, Caleb Landry Jones",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama", "Comedy"],
    },
    {
        "title": "Coco",
        "release_year": 2017,
        "release_date": date(2017, 11, 22),
        "runtime_minutes": 105,
        "age_rating": "PG",
        "synopsis": "A young boy in Mexico, secretly obsessed with music, is transported into the Land of the Dead on Día de los Muertos and uncovers his family's hidden history.",
        "director_name": "Lee Unkrich",
        "cast_text": "Anthony Gonzalez, Gael García Bernal, Benjamin Bratt, Alanna Ubach",
        "language": "en", "country": "US",
        "genres": ["Animation", "Adventure", "Comedy", "Drama"],
    },
    {
        "title": "Roma",
        "release_year": 2018,
        "release_date": date(2018, 8, 30),
        "runtime_minutes": 135,
        "age_rating": "R",
        "synopsis": "A live-in housekeeper for a middle-class family in 1970s Mexico City navigates personal upheaval against a backdrop of national crisis.",
        "director_name": "Alfonso Cuarón",
        "cast_text": "Yalitza Aparicio, Marina de Tavira, Jorge Antonio Guerrero, Fernando Grediaga",
        "language": "es", "country": "MX",
        "genres": ["Drama"],
    },
    {
        "title": "Black Panther",
        "release_year": 2018,
        "release_date": date(2018, 2, 16),
        "runtime_minutes": 134,
        "age_rating": "PG-13",
        "synopsis": "The new king of a technologically advanced African nation faces a rival who would force the country onto the world stage as a militant power.",
        "director_name": "Ryan Coogler",
        "cast_text": "Chadwick Boseman, Michael B. Jordan, Lupita Nyong'o, Danai Gurira, Letitia Wright",
        "language": "en", "country": "US",
        "genres": ["Action", "Adventure", "Sci-Fi"],
    },
    {
        "title": "A Quiet Place",
        "release_year": 2018,
        "release_date": date(2018, 4, 6),
        "runtime_minutes": 90,
        "age_rating": "PG-13",
        "synopsis": "A family lives in near-total silence on a remote farm, hunted by blind creatures that attack anything that makes a sound.",
        "director_name": "John Krasinski",
        "cast_text": "Emily Blunt, John Krasinski, Millicent Simmonds, Noah Jupe",
        "language": "en", "country": "US",
        "genres": ["Horror", "Thriller", "Sci-Fi"],
    },
    {
        "title": "1917",
        "release_year": 2019,
        "release_date": date(2019, 12, 25),
        "runtime_minutes": 119,
        "age_rating": "R",
        "synopsis": "Two young British soldiers are given a near-impossible mission across no man's land in WWI, filmed to look like a single continuous shot.",
        "director_name": "Sam Mendes",
        "cast_text": "George MacKay, Dean-Charles Chapman, Mark Strong, Andrew Scott, Benedict Cumberbatch",
        "language": "en", "country": "GB",
        "genres": ["Drama", "Action"],
    },
    {
        "title": "Marriage Story",
        "release_year": 2019,
        "release_date": date(2019, 11, 6),
        "runtime_minutes": 137,
        "age_rating": "R",
        "synopsis": "A theatre director and an actress try to navigate divorce and bicoastal custody of their son without losing themselves.",
        "director_name": "Noah Baumbach",
        "cast_text": "Adam Driver, Scarlett Johansson, Laura Dern, Alan Alda, Ray Liotta",
        "language": "en", "country": "US",
        "genres": ["Drama", "Romance"],
    },
    {
        "title": "Joker",
        "release_year": 2019,
        "release_date": date(2019, 10, 4),
        "runtime_minutes": 122,
        "age_rating": "R",
        "synopsis": "A failed Gotham comedian and party clown spirals into madness and is reborn as the city's most infamous criminal.",
        "director_name": "Todd Phillips",
        "cast_text": "Joaquin Phoenix, Robert De Niro, Zazie Beetz, Frances Conroy",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama", "Thriller"],
    },
    {
        "title": "Portrait of a Lady on Fire",
        "release_year": 2019,
        "release_date": date(2019, 9, 18),
        "runtime_minutes": 121,
        "age_rating": "R",
        "synopsis": "On a windswept island in 18th-century Brittany, a painter is hired to secretly produce the wedding portrait of a young woman who refuses to sit.",
        "director_name": "Céline Sciamma",
        "cast_text": "Noémie Merlant, Adèle Haenel, Luàna Bajrami, Valeria Golino",
        "language": "fr", "country": "FR",
        "genres": ["Romance", "Drama"],
    },

    # ─── 2020s ────────────────────────────────────────
    {
        "title": "Tenet",
        "release_year": 2020,
        "release_date": date(2020, 9, 3),
        "runtime_minutes": 150,
        "age_rating": "PG-13",
        "synopsis": "A nameless secret agent learns to move through inverted time to prevent a future war that's already partially happened.",
        "director_name": "Christopher Nolan",
        "cast_text": "John David Washington, Robert Pattinson, Elizabeth Debicki, Kenneth Branagh",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Action", "Thriller"],
    },
    {
        "title": "Sound of Metal",
        "release_year": 2020,
        "release_date": date(2020, 11, 20),
        "runtime_minutes": 120,
        "age_rating": "R",
        "synopsis": "A drummer in a metal duo abruptly loses his hearing and must rebuild his sense of self in a recovery community for the deaf.",
        "director_name": "Darius Marder",
        "cast_text": "Riz Ahmed, Olivia Cooke, Paul Raci, Lauren Ridloff",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Nomadland",
        "release_year": 2020,
        "release_date": date(2020, 9, 11),
        "runtime_minutes": 107,
        "age_rating": "R",
        "synopsis": "After losing everything in the Great Recession, a woman lives in her van and drifts across the American West taking seasonal work.",
        "director_name": "Chloé Zhao",
        "cast_text": "Frances McDormand, David Strathairn, Linda May, Charlene Swankie",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Promising Young Woman",
        "release_year": 2020,
        "release_date": date(2020, 12, 25),
        "runtime_minutes": 113,
        "age_rating": "R",
        "synopsis": "A woman with a traumatic past spends her nights setting elaborate traps for men who think she's drunk and helpless.",
        "director_name": "Emerald Fennell",
        "cast_text": "Carey Mulligan, Bo Burnham, Alison Brie, Clancy Brown, Laverne Cox",
        "language": "en", "country": "US",
        "genres": ["Thriller", "Crime", "Drama"],
    },
    {
        "title": "Spencer",
        "release_year": 2021,
        "release_date": date(2021, 11, 5),
        "runtime_minutes": 117,
        "age_rating": "R",
        "synopsis": "Three days at the Sandringham Christmas of 1991 imagined from the inside of Princess Diana's unravelling marriage to the Crown.",
        "director_name": "Pablo Larraín",
        "cast_text": "Kristen Stewart, Jack Farthing, Sally Hawkins, Timothy Spall",
        "language": "en", "country": "GB",
        "genres": ["Drama"],
    },
    {
        "title": "Drive My Car",
        "release_year": 2021,
        "release_date": date(2021, 8, 20),
        "runtime_minutes": 179,
        "age_rating": "R",
        "synopsis": "A widowed theatre director directing a multilingual production of Uncle Vanya finds an unexpected confidant in his assigned young chauffeur.",
        "director_name": "Ryusuke Hamaguchi",
        "cast_text": "Hidetoshi Nishijima, Tōko Miura, Reika Kirishima, Park Yu-rim",
        "language": "ja", "country": "JP",
        "genres": ["Drama"],
    },
    {
        "title": "The Power of the Dog",
        "release_year": 2021,
        "release_date": date(2021, 9, 1),
        "runtime_minutes": 126,
        "age_rating": "R",
        "synopsis": "A domineering rancher torments his brother's new wife and her sensitive son — but the boy is not what he seems.",
        "director_name": "Jane Campion",
        "cast_text": "Benedict Cumberbatch, Kirsten Dunst, Jesse Plemons, Kodi Smit-McPhee",
        "language": "en", "country": "NZ",
        "genres": ["Drama", "Romance"],
    },
    {
        "title": "The Northman",
        "release_year": 2022,
        "release_date": date(2022, 4, 22),
        "runtime_minutes": 137,
        "age_rating": "R",
        "synopsis": "A Viking prince, robbed of his throne and family as a boy, spends decades preparing to take a brutal revenge on his uncle.",
        "director_name": "Robert Eggers",
        "cast_text": "Alexander Skarsgård, Nicole Kidman, Claes Bang, Anya Taylor-Joy, Ethan Hawke",
        "language": "en", "country": "US",
        "genres": ["Action", "Adventure", "Drama"],
    },
    {
        "title": "The Banshees of Inisherin",
        "release_year": 2022,
        "release_date": date(2022, 10, 21),
        "runtime_minutes": 114,
        "age_rating": "R",
        "synopsis": "On a small Irish island in 1923, one lifelong friend tells the other that they're no longer friends, and refuses to explain why.",
        "director_name": "Martin McDonagh",
        "cast_text": "Colin Farrell, Brendan Gleeson, Kerry Condon, Barry Keoghan",
        "language": "en", "country": "IE",
        "genres": ["Comedy", "Drama"],
    },
    {
        "title": "Top Gun: Maverick",
        "release_year": 2022,
        "release_date": date(2022, 5, 27),
        "runtime_minutes": 130,
        "age_rating": "PG-13",
        "synopsis": "Thirty-six years after the original mission, a now-veteran fighter pilot trains a new generation of TOP GUN graduates for a near-suicidal raid.",
        "director_name": "Joseph Kosinski",
        "cast_text": "Tom Cruise, Miles Teller, Jennifer Connelly, Glen Powell, Jon Hamm",
        "language": "en", "country": "US",
        "genres": ["Action", "Drama"],
    },
    {
        "title": "The Menu",
        "release_year": 2022,
        "release_date": date(2022, 11, 18),
        "runtime_minutes": 107,
        "age_rating": "R",
        "synopsis": "A young couple travels to a remote island for dinner at an exclusive restaurant, where the celebrated chef has prepared a very particular tasting menu.",
        "director_name": "Mark Mylod",
        "cast_text": "Ralph Fiennes, Anya Taylor-Joy, Nicholas Hoult, Hong Chau, Janet McTeer",
        "language": "en", "country": "US",
        "genres": ["Horror", "Comedy", "Thriller"],
    },
    {
        "title": "Tár",
        "release_year": 2022,
        "release_date": date(2022, 10, 7),
        "runtime_minutes": 158,
        "age_rating": "R",
        "synopsis": "A celebrated conductor at the height of her powers begins to lose her grip as accusations from her past close in around her.",
        "director_name": "Todd Field",
        "cast_text": "Cate Blanchett, Nina Hoss, Noémie Merlant, Sophie Kauer",
        "language": "en", "country": "US",
        "genres": ["Drama"],
    },
    {
        "title": "Past Lives",
        "release_year": 2023,
        "release_date": date(2023, 6, 2),
        "runtime_minutes": 105,
        "age_rating": "PG-13",
        "synopsis": "Two childhood sweethearts in Seoul are separated when one family emigrates to America. Twenty years later they reunite in New York for a single, fraught week.",
        "director_name": "Celine Song",
        "cast_text": "Greta Lee, Teo Yoo, John Magaro",
        "language": "en", "country": "US",
        "genres": ["Drama", "Romance"],
    },
    {
        "title": "Oppenheimer",
        "release_year": 2023,
        "release_date": date(2023, 7, 21),
        "runtime_minutes": 180,
        "age_rating": "R",
        "synopsis": "The American physicist who led the Manhattan Project builds the atomic bomb, then watches as the political establishment turns on him.",
        "director_name": "Christopher Nolan",
        "cast_text": "Cillian Murphy, Emily Blunt, Robert Downey Jr., Matt Damon, Florence Pugh",
        "language": "en", "country": "US",
        "genres": ["Drama", "Thriller"],
    },
    {
        "title": "Anatomy of a Fall",
        "release_year": 2023,
        "release_date": date(2023, 8, 23),
        "runtime_minutes": 152,
        "age_rating": "R",
        "synopsis": "A writer is put on trial for her husband's mysterious death in their snowbound Alpine chalet, with their visually impaired son the only witness.",
        "director_name": "Justine Triet",
        "cast_text": "Sandra Hüller, Swann Arlaud, Milo Machado-Graner, Antoine Reinartz",
        "language": "fr", "country": "FR",
        "genres": ["Drama", "Mystery", "Thriller"],
    },
    {
        "title": "Killers of the Flower Moon",
        "release_year": 2023,
        "release_date": date(2023, 10, 20),
        "runtime_minutes": 206,
        "age_rating": "R",
        "synopsis": "In 1920s Oklahoma, members of the oil-rich Osage Nation are murdered one by one as a former soldier marries into the family.",
        "director_name": "Martin Scorsese",
        "cast_text": "Leonardo DiCaprio, Robert De Niro, Lily Gladstone, Jesse Plemons",
        "language": "en", "country": "US",
        "genres": ["Crime", "Drama"],
    },
    {
        "title": "Poor Things",
        "release_year": 2023,
        "release_date": date(2023, 12, 8),
        "runtime_minutes": 141,
        "age_rating": "R",
        "synopsis": "A Victorian woman brought back from the dead with the brain of an infant grows rapidly, escapes her creator, and sets off across Europe on her own terms.",
        "director_name": "Yorgos Lanthimos",
        "cast_text": "Emma Stone, Mark Ruffalo, Willem Dafoe, Ramy Youssef",
        "language": "en", "country": "IE",
        "genres": ["Comedy", "Drama", "Sci-Fi", "Romance"],
    },
    {
        "title": "The Holdovers",
        "release_year": 2023,
        "release_date": date(2023, 10, 27),
        "runtime_minutes": 133,
        "age_rating": "R",
        "synopsis": "A grumpy classics teacher at a New England boarding school is stuck supervising the students who can't go home for Christmas break in 1970.",
        "director_name": "Alexander Payne",
        "cast_text": "Paul Giamatti, Da'Vine Joy Randolph, Dominic Sessa, Carrie Preston",
        "language": "en", "country": "US",
        "genres": ["Comedy", "Drama"],
    },
    {
        "title": "Dune: Part Two",
        "release_year": 2024,
        "release_date": date(2024, 3, 1),
        "runtime_minutes": 166,
        "age_rating": "PG-13",
        "synopsis": "Paul Atreides unites with the Fremen of Arrakis to wage a holy war against the houses that destroyed his family.",
        "director_name": "Denis Villeneuve",
        "cast_text": "Timothée Chalamet, Zendaya, Rebecca Ferguson, Javier Bardem, Austin Butler, Florence Pugh",
        "language": "en", "country": "US",
        "genres": ["Sci-Fi", "Adventure", "Drama"],
    },

]


# Reviews — (user, movie, rating 1-10, body, contains_spoilers, days_ago)
REVIEWS = [
    # Inception — 3 reviews
    ("alex_chen", "Inception", 9, "Saw this in cinemas at 19 and it broke my brain in the best way. The hotel hallway scene is one of the most iconic action sequences of the 2010s, full stop. Not perfect — the third act gets bogged down in exposition — but everything else more than compensates.", False, 30),
    ("sarah_kim", "Inception", 7, "I've come back to this three times now and I'm still not convinced the emotional core works. Cobb's grief feels like a plot device rather than a character. Beautiful filmmaking though.", False, 45),
    ("filmcritic99", "Inception", 9, "Nolan's cleanest blockbuster — every shot is in service of the story, every line of dialogue earns its place. The much-debated ending isn't ambiguous if you're paying attention to Cobb's wedding ring.", True, 60),

    # Parasite — 5 reviews (most popular)
    ("alex_chen", "Parasite", 10, "First foreign-language film to win Best Picture and you can see exactly why. Bong Joon-ho controls tone like a conductor — comedy, tragedy, horror, all in the same scene sometimes. The basement reveal is one of the most stomach-dropping moments I've experienced in a theatre.", True, 25),
    ("filmcritic99", "Parasite", 10, "Class commentary that actually has teeth. The Park family aren't villains — that's what makes them so devastating. They're just people who've forgotten that other people exist.", False, 35),
    ("sarah_kim", "Parasite", 9, "This deserved every award it got. I keep thinking about the rain scene — same storm, two completely different experiences.", False, 22),
    ("jordan_lee", "Parasite", 9, "The third act tonal shift is so brutal. I was laughing one minute and then suddenly nobody was safe. Bong is just operating on a different level than everyone else.", False, 18),
    ("maya_patel", "Parasite", 8, "Watched it last week. Worth the hype. That's all I'll say.", False, 7),

    # Shawshank — 4 reviews
    ("alex_chen", "The Shawshank Redemption", 10, "It's the one everyone's seen and yet somehow still underrated. Tim Robbins' restraint as Andy is the whole movie — Morgan Freeman's narration would fall flat without it.", False, 50),
    ("filmcritic99", "The Shawshank Redemption", 10, "The best film about hope ever made, full stop. Every time I think I've outgrown it I'll catch ten minutes on TV and remember why it's been at the top of every list since 1994.", False, 70),
    ("sarah_kim", "The Shawshank Redemption", 8, "Beautiful, but maybe a bit too neat? Real prison stories don't end with sandy beaches. Still — Freeman's voice carrying the whole thing is undeniable.", False, 55),
    ("jordan_lee", "The Shawshank Redemption", 10, "Watched it for the first time at 30 because everyone made fun of me for not having seen it. They were right. Cried twice.", False, 40),

    # Dark Knight — 2 reviews
    ("alex_chen", "The Dark Knight", 9, "Heath Ledger's performance is the only reason superhero movies are taken seriously now. The interrogation scene alone deserves a film studies course. Can't quite go to 10 because the third act drags but that's nitpicking.", False, 48),
    ("filmcritic99", "The Dark Knight", 10, "The Joker is the only superhero villain who ever felt like a real threat. Ledger plays him as if he genuinely doesn't know what he's going to do next, and neither does the audience.", False, 65),

    # Mad Max — 2 reviews
    ("alex_chen", "Mad Max: Fury Road", 9, "Ninety percent practical effects. They actually built and crashed those vehicles. You can feel it in every frame, and that's why CGI-heavy action movies feel so weightless by comparison now.", False, 38),
    ("jordan_lee", "Mad Max: Fury Road", 10, "The Doof Warrior. That's the whole review. They put a flame-throwing guitar guy on a truck full of speakers leading the war party. Cinema.", False, 33),

    # Get Out — 3 reviews
    ("alex_chen", "Get Out", 9, "Jordan Peele turns a simple premise into a genuine horror landmark. The 'sunken place' is the kind of metaphor that you keep thinking about for weeks.", False, 42),
    ("jordan_lee", "Get Out", 10, "Best horror debut of the 2010s. Peele understood that the scariest monsters are people who think they're the good guys.", False, 36),
    ("sarah_kim", "Get Out", 9, "Watched it again last month with my partner who hadn't seen it. Even knowing the twist, the dread in the first hour is suffocating. Important film.", True, 28),

    # Spider-Verse — 3 reviews
    ("filmcritic99", "Spider-Man: Into the Spider-Verse", 10, "Visually the most innovative animated film since Akira. Every frame looks like a comic page in motion. Doesn't matter if you've never read a Spider-Man comic — the film teaches you the language as it goes.", False, 52),
    ("alex_chen", "Spider-Man: Into the Spider-Verse", 9, "Took my niece to this thinking it'd be fine and ended up loving it more than her. Miles Morales is the best Spider-Man, fight me.", False, 44),
    ("maya_patel", "Spider-Man: Into the Spider-Verse", 8, "My boyfriend made me watch it. Reluctantly amazing.", False, 5),

    # LotR — 3 reviews
    ("alex_chen", "The Lord of the Rings: The Fellowship of the Ring", 10, "The Council of Elrond scene is the reason I started reading the books. Twenty minutes of people in a circle talking and it's electrifying. Howard Shore's score is the real fellowship.", False, 80),
    ("filmcritic99", "The Lord of the Rings: The Fellowship of the Ring", 10, "Peter Jackson did the impossible — adapted Tolkien without losing the soul. Twenty-plus years on it still doesn't feel dated, which is a miracle for a CGI-heavy movie of that era.", False, 90),
    ("sarah_kim", "The Lord of the Rings: The Fellowship of the Ring", 9, "The pacing in the extended cut works for me, the theatrical cut feels rushed. Either way, Boromir's death scene is one of the best deaths in the trilogy.", True, 75),

    # Spirited Away — 2 reviews
    ("alex_chen", "Spirited Away", 10, "Everything Miyazaki does is great but this is the one I keep returning to. The bathhouse setting is so densely imagined it feels like a real place that just happens to exist in another dimension.", False, 56),
    ("sarah_kim", "Spirited Away", 9, "Watched it dubbed as a kid, then subbed as an adult. Two completely different films. The Japanese voice cast carries so much more melancholy.", False, 49),

    # La La Land — 2 reviews
    ("filmcritic99", "La La Land", 7, "Chazelle's love letter to old Hollywood works best when it's at its most artificial — the planetarium dance sequence is a masterpiece. Less convinced by the relationship drama.", False, 58),
    ("alex_chen", "La La Land", 8, "I was ready to hate this and then the opening number happened. Got me. The ending is devastating in the best way.", True, 32),

    # Interstellar — 2 reviews
    ("filmcritic99", "Interstellar", 8, "Nolan's most ambitious work and his most uneven. The spectacle is stunning, the science is mostly defensible, but the third act metaphysics asked me to feel something I couldn't quite reach.", False, 62),
    ("alex_chen", "Interstellar", 9, "The docking scene. Hans Zimmer's score in that scene. That's enough.", False, 40),

    # Whiplash — 2 reviews
    ("filmcritic99", "Whiplash", 10, "Chazelle's debut is harder, leaner, more honest than his musicals. The final drum solo is a thirteen-minute argument about what art costs.", False, 68),
    ("alex_chen", "Whiplash", 9, "Watched this back to back with Black Swan once and didn't sleep that night. Films about obsession should make you feel obsessive.", False, 46),

    # Knives Out — 1 review
    ("filmcritic99", "Knives Out", 8, "Rian Johnson clearly grew up reading Agatha Christie and finally got to make his own. Cool fun, beautifully shot, Daniel Craig's accent is a small national treasure.", False, 53),

    # Lady Bird — 1 review
    ("sarah_kim", "Lady Bird", 9, "Greta Gerwig somehow made every fight I had with my mom in 2008 feel universal. Saoirse Ronan deserves all the awards she didn't get for this.", False, 39),

    # Hereditary — 1 review
    ("jordan_lee", "Hereditary", 9, "Aster's debut is more grief than horror, which is what makes it so unsettling. Toni Collette is doing things in this performance that haven't been done before.", False, 31),

    # Bridesmaids — 1 review
    ("filmcritic99", "Bridesmaids", 8, "Better than it had any right to be. Kristen Wiig's Annie is one of the great comedic performances of the decade — completely lived-in misery played as comedy.", False, 47),

    # Moonlight — 2 reviews
    ("filmcritic99", "Moonlight", 10, "Three chapters, three actors playing the same character, one of the most cohesive performances ever assembled. Barry Jenkins works in moments that other directors throw away.", False, 72),
    ("alex_chen", "Moonlight", 10, "The diner scene. That's all I need to say.", False, 41),

    # Dune — 2 reviews
    ("maya_patel", "Dune", 7, "Visually overwhelming. I think I need to read the book? Going to give it another watch when Part Two streams.", False, 4),
    ("filmcritic99", "Dune", 9, "Villeneuve does what David Lynch couldn't — turns the unfilmable into something cinematic. The score, the scale, the patience. Bring on Part Two.", False, 26),

    ("filmcritic99", "The Godfather", 10, "Coppola's masterpiece, full stop. Every shot, every line of dialogue, every cut — the entire vocabulary of modern cinema is in here. Pacino's transformation in the restaurant scene is one of the great acting moments on film.", False, 95),
    ("alex_chen", "The Godfather", 10, "Watched this with my dad when I was a teenager and we both went quiet for ten minutes after the ending. Some movies are bigger than the screen.", True, 88),

    ("alex_chen", "Pulp Fiction", 9, "The dialogue. The structure. The needle scene. Tarantino's most rewatchable film and arguably his best. The fact that we follow Vincent for half the movie knowing what's coming is just chef's kiss.", True, 70),
    ("sarah_kim", "Pulp Fiction", 8, "Brilliantly written but the back half drags slightly in my opinion. The Mia/Vincent date sequence justifies the whole thing though.", False, 65),

    ("filmcritic99", "Goodfellas", 10, "Scorsese at the absolute peak of his powers. The long Copacabana take is so often imitated that it's easy to forget how revolutionary it actually was in 1990.", False, 80),
    ("jordan_lee", "Goodfellas", 10, "'As far back as I can remember' — best opening line in cinema. Pesci is terrifying. Bracco never gets enough credit.", False, 75),

    ("filmcritic99", "The Matrix", 10, "Pre-everything internet culture has appropriated The Matrix for. Just a perfect piece of 1999 sci-fi action — the lobby scene, the bullet time, the questions it asks. Aged better than almost any movie of that era.", False, 78),
    ("alex_chen", "The Matrix", 9, "Showed this to my nephew last year, his only point of reference for 'realistic' CGI was the Avengers. He was genuinely stunned by what they pulled off with practical effects + computer assistance in 1999.", False, 50),

    ("alex_chen", "Fight Club", 8, "Holds up better than its meme reputation would suggest. The book is better but Fincher gets so much of the texture right. The Ikea apartment scene is everything.", False, 55),
    ("filmcritic99", "Fight Club", 9, "A movie that's been misunderstood by every generation that watched it. Tyler Durden is the villain, gentlemen.", True, 72),

    ("filmcritic99", "Citizen Kane", 10, "Still the answer to 'what's the greatest film ever made?' and it's not just nostalgia talking. Welles invented half the visual language of the medium in one go.", False, 100),

    ("filmcritic99", "2001: A Space Odyssey", 10, "Kubrick made a movie that asks you to do half the work. If you meet it on its terms, there's nothing else like it. If you don't, it's the most boring film ever made. I love that.", False, 110),
    ("alex_chen", "2001: A Space Odyssey", 8, "The Star Gate sequence is incredible. The middle hour with HAL is incredible. The opening hour with the apes I keep nodding off to. Sorry Stanley.", False, 60),

    ("alex_chen", "Blade Runner", 9, "Watched the Final Cut for the first time last year and finally got what people meant. The atmosphere is the entire point — every frame looks like a painting.", False, 48),

    ("filmcritic99", "Eternal Sunshine of the Spotless Mind", 10, "Charlie Kaufman's best screenplay. The fact that Jim Carrey of all people gives the most heartbroken performance of the 2000s in this is still surprising to me.", False, 85),
    ("sarah_kim", "Eternal Sunshine of the Spotless Mind", 10, "The beach house collapsing scene. I think about it every six months.", True, 67),

    ("filmcritic99", "There Will Be Blood", 10, "Day-Lewis at full thunder. The ending is one of those cinema scenes where you're not sure if you should laugh or get up and leave.", True, 76),

    ("alex_chen", "Drive", 9, "Style over substance and proud of it. Gosling barely speaks for the first thirty minutes and it works because Refn understands silence is louder than monologue.", False, 42),

    ("alex_chen", "Her", 10, "Jonze made a movie about loneliness in 2013 that predicted exactly how 2020s technology would make us feel. Phoenix's face in the final scene is wrecked.", False, 38),
    ("sarah_kim", "Her", 9, "The pants. The high-waisted pants are the production design choice that sells the entire near-future Los Angeles.", False, 33),

    ("filmcritic99", "Arrival", 10, "Villeneuve's best work and the most emotionally devastating sci-fi of the decade. Adams was robbed at the Oscars.", True, 70),

    ("jordan_lee", "The Witch", 9, "Eggers' debut. Period-accurate dialogue, period-accurate folklore, period-accurate dread. The goat. The ending. Black Phillip, my king.", True, 40),

    ("alex_chen", "Past Lives", 10, "Watched it in cinemas with my partner. We sat in silence in the car park for ten minutes afterwards. That's all I have to say.", False, 18),
    ("sarah_kim", "Past Lives", 10, "Greta Lee carries this without ever raising her voice. Some films don't need plot, just two people in a bar grappling with the lives they didn't live.", False, 22),

    ("filmcritic99", "Oppenheimer", 9, "Nolan's most mature work. Less interested in the spectacle of the bomb than in the political bureaucracy that punished the man who built it. The closing shot.", True, 28),
    ("alex_chen", "Oppenheimer", 9, "Three hours that fly. Murphy holds the centre of every scene by just standing still and absorbing. Saw it in IMAX 70mm and the Trinity sequence was the loudest silence I've heard in a cinema.", False, 26),

    ("filmcritic99", "The Banshees of Inisherin", 10, "McDonagh's quietest film and his best. Two men and a small misunderstanding that grows like rust. Brutal and very, very funny.", False, 45),

    ("filmcritic99", "Poor Things", 9, "Lanthimos finally working at scale. Stone is committed in a way that should embarrass other actors. Funniest film of 2023.", False, 30),
    ("maya_patel", "Poor Things", 8, "Weird. I think I liked it? Going to need to think about it.", False, 19),

    ("filmcritic99", "The Lion King", 9, "The Disney peak. Mufasa's death is still the most efficient gut punch in any kids' movie. Hamlet but the prince is a lion and Iago is a hyena.", True, 90),

    ("alex_chen", "Hot Fuzz", 9, "Edgar Wright is the only director who edits his comedies like they're action movies. The result is the funniest film of the 2000s, fight me.", False, 52),

    ("sarah_kim", "Portrait of a Lady on Fire", 10, "The most stunning movie I've seen this decade. Every shot is a painting; every silence is louder than dialogue. The ending sequence at the orchestra is devastating.", False, 35),

    ("filmcritic99", "Tár", 9, "Cate Blanchett is doing something almost mystical here. The film refuses to tell you whether to root for her or revile her, which is the whole point.", False, 32),

]


# Watchlist — (user, movie, notes, days_ago)
WATCHLIST = [
    ("alex_chen", "John Wick", None, 14),
    ("alex_chen", "Blade Runner 2049", "Need to rewatch the original first", 12),
    ("alex_chen", "Toy Story", "for nostalgia night", 8),
    ("alex_chen", "Everything Everywhere All at Once", None, 21),
    ("alex_chen", "The Grand Budapest Hotel", None, 15),
    ("alex_chen", "Bridesmaids", "for movie night with M", 3),

    ("sarah_kim", "The Babadook", "if I'm brave enough", 19),
    ("sarah_kim", "John Wick", None, 11),
    ("sarah_kim", "Dune", "Boyfriend keeps recommending", 9),
    ("sarah_kim", "Everything Everywhere All at Once", None, 6),

    ("filmcritic99", "The Babadook", None, 23),
    ("filmcritic99", "Toy Story", "Pixar retrospective", 17),
    ("filmcritic99", "No Country for Old Men", "Owe an essay on this", 13),

    ("jordan_lee", "La La Land", "expanding my horizons", 7),
    ("jordan_lee", "Lady Bird", None, 5),

    # maya_patel: empty watchlist (edge case)
    # ghost_user: empty (edge case)
]


# Follows — (follower, followed, days_ago)
FOLLOWS = [
    ("alex_chen", "sarah_kim", 200),
    ("sarah_kim", "alex_chen", 195),     # mutual with above
    ("alex_chen", "filmcritic99", 300),
    ("filmcritic99", "alex_chen", 290),  # mutual with above
    ("alex_chen", "jordan_lee", 120),
    ("sarah_kim", "filmcritic99", 250),
    ("sarah_kim", "jordan_lee", 150),
    ("jordan_lee", "filmcritic99", 160),
    ("maya_patel", "alex_chen", 10),
    ("maya_patel", "filmcritic99", 8),
    # ghost_user: follows nobody, followed by nobody (edge case)
]


# Likes — (liker, review_author, review_movie, days_ago)
LIKES = [
    # filmcritic99's Parasite review — very popular
    ("sarah_kim", "filmcritic99", "Parasite", 30),
    ("jordan_lee", "filmcritic99", "Parasite", 28),
    ("alex_chen", "filmcritic99", "Parasite", 33),
    ("maya_patel", "filmcritic99", "Parasite", 5),

    # filmcritic99's Spider-Verse review — popular
    ("alex_chen", "filmcritic99", "Spider-Man: Into the Spider-Verse", 50),
    ("maya_patel", "filmcritic99", "Spider-Man: Into the Spider-Verse", 4),
    ("sarah_kim", "filmcritic99", "Spider-Man: Into the Spider-Verse", 48),
    ("jordan_lee", "filmcritic99", "Spider-Man: Into the Spider-Verse", 45),

    # sarah_kim's Lady Bird — moderately liked
    ("alex_chen", "sarah_kim", "Lady Bird", 35),
    ("jordan_lee", "sarah_kim", "Lady Bird", 30),
    ("filmcritic99", "sarah_kim", "Lady Bird", 38),

    # filmcritic99's Inception — modest likes
    ("alex_chen", "filmcritic99", "Inception", 55),
    ("sarah_kim", "filmcritic99", "Inception", 50),

    # alex_chen's Inception — modest
    ("filmcritic99", "alex_chen", "Inception", 28),
    ("sarah_kim", "alex_chen", "Inception", 25),

    # filmcritic99's Whiplash — modest
    ("alex_chen", "filmcritic99", "Whiplash", 65),
    ("sarah_kim", "filmcritic99", "Whiplash", 60),

    # filmcritic99's Moonlight
    ("alex_chen", "filmcritic99", "Moonlight", 70),
    ("sarah_kim", "filmcritic99", "Moonlight", 65),

    # jordan's Hereditary
    ("filmcritic99", "jordan_lee", "Hereditary", 28),
    ("alex_chen", "jordan_lee", "Hereditary", 25),

    # alex_chen's Mad Max
    ("filmcritic99", "alex_chen", "Mad Max: Fury Road", 36),
    ("jordan_lee", "alex_chen", "Mad Max: Fury Road", 34),

    # singletons
    ("alex_chen", "sarah_kim", "Get Out", 27),
    ("sarah_kim", "alex_chen", "Spirited Away", 50),
]


# Comments — (author, review_author, review_movie, body, parent_index_or_None, days_ago)
# Index refers to the position of an earlier comment in this list (for replies).
COMMENTS = [
    # 0 — top-level on filmcritic99's Parasite review
    ("alex_chen", "filmcritic99", "Parasite", "100% agree on the Park family being the saddest thing about it. They're not even cruel — just oblivious.", None, 27),
    # 1 — reply to comment 0
    ("filmcritic99", "filmcritic99", "Parasite", "Bingo. Cruelty would have been easier to watch.", 0, 26),
    # 2 — top-level on the same review (separate thread)
    ("jordan_lee", "filmcritic99", "Parasite", "The basement reveal made me audibly gasp in the cinema.", None, 24),
    # 3 — top-level on alex's Inception review
    ("sarah_kim", "alex_chen", "Inception", "Came round to this take on rewatch. The third act IS slow.", None, 20),
    # 4 — reply to comment 3
    ("alex_chen", "alex_chen", "Inception", "Right? Glad I'm not crazy.", 3, 19),
    # 5 — top-level on jordan's Hereditary review
    ("alex_chen", "jordan_lee", "Hereditary", "Toni Collette deserved an Oscar nomination for this. The dinner table scene alone.", None, 22),
    # 6 — top-level on sarah's Lady Bird review
    ("filmcritic99", "sarah_kim", "Lady Bird", "She's been cheated out of awards her whole career. This is the most criminal one.", None, 36),
    # 7 — top-level on filmcritic99's Spider-Verse review
    ("maya_patel", "filmcritic99", "Spider-Man: Into the Spider-Verse", "Just watched. Best animation I've ever seen.", None, 3),
]


# ─── Clearing ─────────────────────────────────────────────────────────


def _clear():
    """Delete all rows from seed-affected tables in FK-safe order.

    Comments use a self-referential FK (replies → parents), so we delete
    replies first before deleting top-level comments.
    """
    # Comment replies first, then top-level comments
    ReviewComment.query.filter(ReviewComment.parent_comment_id.isnot(None)).delete(
        synchronize_session=False
    )
    db.session.flush()
    ReviewComment.query.delete(synchronize_session=False)

    ReviewLike.query.delete(synchronize_session=False)
    WatchlistItem.query.delete(synchronize_session=False)
    Follow.query.delete(synchronize_session=False)
    Review.query.delete(synchronize_session=False)

    # Association table — must clear before deleting movies/genres
    db.session.execute(movie_genres.delete())

    Movie.query.delete(synchronize_session=False)
    Genre.query.delete(synchronize_session=False)
    User.query.delete(synchronize_session=False)
    db.session.commit()


# ─── Builders ─────────────────────────────────────────────────────────


def _create_genres():
    genres = {}
    for name in GENRE_NAMES:
        g = Genre(name=name)
        db.session.add(g)
        genres[name] = g
    db.session.flush()
    return genres


def _create_users():
    users = {}
    for spec in USERS:
        joined = _ago(spec["joined_days_ago"])
        u = User(
            username=spec["username"],
            email=spec["email"],
            bio=spec.get("bio"),
            created_at=joined,
            updated_at=joined,
            is_active=True,
        )
        u.set_password("password123")
        db.session.add(u)
        users[spec["username"]] = u
    db.session.flush()
    return users


def _create_movies(genre_lookup):
    movies = {}
    for spec in MOVIES:
        m = Movie(
            title=spec["title"],
            release_year=spec["release_year"],
            release_date=spec["release_date"],
            runtime_minutes=spec["runtime_minutes"],
            age_rating=spec["age_rating"],
            synopsis=spec["synopsis"],
            poster_path=_poster(spec["title"]),
            backdrop_path=None,
            director_name=spec["director_name"],
            cast_text=spec["cast_text"],
            language=spec["language"],
            country=spec["country"],
            tmdb_id=spec.get("tmdb_id"),
        )
        m.genres = [genre_lookup[g] for g in spec["genres"]]
        db.session.add(m)
        movies[spec["title"]] = m
    db.session.flush()
    return movies


def _create_reviews(user_lookup, movie_lookup):
    reviews = {}
    for username, movie_title, rating, body, spoilers, days_ago in REVIEWS:
        ts = _ago(days_ago)
        r = Review(
            user_id=user_lookup[username].id,
            movie_id=movie_lookup[movie_title].id,
            rating=rating,
            body=body,
            contains_spoilers=spoilers,
            created_at=ts,
            updated_at=ts,
        )
        db.session.add(r)
        reviews[(username, movie_title)] = r
    db.session.flush()
    return reviews


def _create_watchlist(user_lookup, movie_lookup):
    for username, movie_title, notes, days_ago in WATCHLIST:
        item = WatchlistItem(
            user_id=user_lookup[username].id,
            movie_id=movie_lookup[movie_title].id,
            notes=notes,
            created_at=_ago(days_ago),
        )
        db.session.add(item)


def _create_follows(user_lookup):
    for follower, followed, days_ago in FOLLOWS:
        f = Follow(
            follower_id=user_lookup[follower].id,
            followed_id=user_lookup[followed].id,
            created_at=_ago(days_ago),
        )
        db.session.add(f)


def _create_likes(user_lookup, review_lookup):
    for liker, review_author, review_movie, days_ago in LIKES:
        like = ReviewLike(
            user_id=user_lookup[liker].id,
            review_id=review_lookup[(review_author, review_movie)].id,
            created_at=_ago(days_ago),
        )
        db.session.add(like)


def _create_comments(user_lookup, review_lookup):
    """Create comments, flushing after each so child comments can reference parents."""
    created = []
    for author, rev_author, rev_movie, body, parent_idx, days_ago in COMMENTS:
        parent_id = created[parent_idx].id if parent_idx is not None else None
        c = ReviewComment(
            user_id=user_lookup[author].id,
            review_id=review_lookup[(rev_author, rev_movie)].id,
            body=body,
            parent_comment_id=parent_id,
            created_at=_ago(days_ago),
            updated_at=_ago(days_ago),
        )
        db.session.add(c)
        db.session.flush()
        created.append(c)


# ─── CLI command ──────────────────────────────────────────────────────


@app.cli.command("seed-db")
def seed_db():
    """Wipe all data and reseed the database with sample content."""
    click.echo("Clearing existing data...")
    _clear()

    click.echo("Creating genres...")
    genres = _create_genres()

    click.echo("Creating users...")
    users = _create_users()

    click.echo("Creating movies...")
    movies = _create_movies(genres)

    click.echo("Creating reviews...")
    reviews = _create_reviews(users, movies)

    click.echo("Creating watchlist items...")
    _create_watchlist(users, movies)

    click.echo("Creating follows...")
    _create_follows(users)

    click.echo("Creating review likes...")
    _create_likes(users, reviews)

    click.echo("Creating review comments...")
    _create_comments(users, reviews)

    db.session.commit()

    click.echo("")
    click.echo("Database seeded.")
    click.echo("")
    click.echo(f"  Users:           {User.query.count()}")
    click.echo(f"  Movies:          {Movie.query.count()}")
    click.echo(f"  Genres:          {Genre.query.count()}")
    click.echo(f"  Reviews:         {Review.query.count()}")
    click.echo(f"  Watchlist items: {WatchlistItem.query.count()}")
    click.echo(f"  Follows:         {Follow.query.count()}")
    click.echo(f"  Review likes:    {ReviewLike.query.count()}")
    click.echo(f"  Comments:        {ReviewComment.query.count()}")
    click.echo("")
    click.echo("Demo accounts (all with password 'password123'):")
    click.echo("  alex@example.com    — most active, lots of reviews + watchlist")
    click.echo("  sarah@example.com   — moderate activity")
    click.echo("  film@example.com    — power critic, many reviews")
    click.echo("  jordan@example.com  — horror fan")
    click.echo("  maya@example.com    — new user, few reviews, empty watchlist")
    click.echo("  ghost@example.com   — empty profile (edge-case test)")
