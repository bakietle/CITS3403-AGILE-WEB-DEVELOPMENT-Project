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
