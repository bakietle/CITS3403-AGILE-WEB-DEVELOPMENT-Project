# 🌟 Movie Star

> A community-driven movie discovery, rating, and review platform.
> Group project for **CITS3403 — Agile Web Development**, The University of Western Australia.

---

## 📖 About

**Movie Star** is a full-stack web application where film fans can discover
movies, rate and review them, build a personal watchlist, and follow other
reviewers. Users can write spoiler-tagged reviews, like and comment on
other people's reviews (with threaded replies), and curate a public
profile.

The app is server-rendered with Flask + Jinja, sprinkled with AJAX for
the interactions that should not trigger a page reload (watchlist
add/remove, review likes, comment posting).

---

## 👥 Team

| Name          | Student ID | GitHub        |
|---------------|------------|---------------|
| Ba Kiet Le    | 24337123   | bakietle      |
| Hogan Tan     | 23644329   | HOGAN-T       |
| Mengfei Chen  | 24011929   | Mengfei-Chen  |
| Wei Bin Ting  | 24033168   | Smolyellow    |

---

## ✨ Features

**Accounts & profiles**
- Sign up, log in, log out (Flask-Login + hashed passwords)
- Edit profile (display name, bio, avatar) and change password
- Public profile pages for other users
- Follow / unfollow other reviewers (with a guard against following yourself)

**Movies & search**
- Home page with a hero search and a "highest rated" grid
- Search with filters (genre, year, minimum rating) and pagination
- Movie detail pages with poster, metadata, average rating, and the
  community's reviews

**Reviews**
- Write, edit, and delete reviews (rating + written body, optional spoiler flag)
- Like and unlike other users' reviews (AJAX, no page reload)
- Comment on reviews and post threaded replies
- Delete your own comments

**Watchlist**
- Add or remove any movie from your personal watchlist (AJAX)
- Dedicated watchlist page

**Under the hood**
- CSRF protection on every state-changing request (Flask-WTF)
- Alembic migrations via Flask-Migrate
- Seed script with demo users, movies, reviews, and watchlist entries
- Optional OMDb integration to fetch movie posters

---

## 🛠️ Tech Stack

| Layer        | Technology                                                    |
|--------------|---------------------------------------------------------------|
| Frontend     | Jinja2 templates, Tailwind CSS, Bootstrap, vanilla JavaScript |
| Backend      | Python 3.8+, Flask                                            |
| Auth         | Flask-Login, Flask-WTF (CSRF), Werkzeug password hashing      |
| ORM / DB     | Flask-SQLAlchemy, SQLite (default)                            |
| Migrations   | Flask-Migrate (Alembic)                                       |
| Testing      | Python `unittest`, Selenium WebDriver (headless Chrome)       |
| External API | OMDb (optional — used only to fetch posters)                  |

---

## 📁 Project Structure

```
CITS3403-AGILE-WEB-DEVELOPMENT-Project/
├─ app/
│  ├─ __init__.py        # Flask app factory, extensions, CSRF, login manager
│  ├─ config.py          # Loads .env, configures SQLAlchemy + SECRET_KEY
│  ├─ auth.py            # /auth, /login, /signup, /logout routes
│  ├─ routes.py          # Pages, search, reviews, watchlist, profiles, follows
│  ├─ models.py          # User, Movie, Genre, Review, ReviewLike,
│  │                     # ReviewComment, WatchlistItem, Follow
│  ├─ forms.py           # Flask-WTF form definitions
│  ├─ seed.py            # `flask seed-db` CLI command (demo data)
│  ├─ posters.py         # `flask fetch-posters` CLI command (OMDb)
│  ├─ app.db             # SQLite database (created by `flask db upgrade`)
│  ├─ templates/         # Jinja2 templates (one .html per page)
│  └─ static/
│     ├─ css/            # One stylesheet per page + shared style.css
│     └─ js/             # One script per page (AJAX, tab toggles, etc.)
├─ migrations/           # Alembic migration history
├─ tests/
│  ├─ test_unit.py       # unittest unit tests (isolated temp SQLite)
│  └─ test_selenium.py   # Selenium end-to-end tests (headless Chrome)
├─ run.py                # Entry point — `python run.py` or `flask run`
├─ requirements.txt
├─ .env.example          # Template for the .env file you create locally
└─ README.md
```

---

## 🚀 Getting Started

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/)
- [Git](https://git-scm.com/)
- Google Chrome (only required for the Selenium tests)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-org>/CITS3403-AGILE-WEB-DEVELOPMENT-Project.git
   cd CITS3403-AGILE-WEB-DEVELOPMENT-Project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     venv\Scripts\activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create your `.env` file**

   Copy the template and fill in the values:
   ```bash
   cp .env.example .env
   ```
   At minimum your `.env` needs:
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=replace-with-your-own-secret-key
   DATABASE_URL=                # leave blank to use the bundled SQLite db
   OMDB_KEY=                    # optional — only needed for `flask fetch-posters`
   ```
   > The app will refuse to start if `SECRET_KEY` is missing. If
   > `DATABASE_URL` is blank, SQLAlchemy falls back to
   > `sqlite:///app/app.db`.

6. **Apply database migrations**
   ```bash
   flask db upgrade
   ```

7. **Seed demo data** (optional but recommended for a first run)
   ```bash
   flask seed-db
   ```

8. **Fetch real movie posters** (optional — requires `OMDB_KEY`)
   ```bash
   flask fetch-posters
   ```
   Without this, movies fall back to placeholder posters. See the
   [Movie Posters](#-movie-posters-omdb) section below for details.

9. **Run the application**
   ```bash
   python run.py
   ```
   or
   ```bash
   flask run
   ```

10. Open your browser at <http://localhost:5000>.

---

## 👤 Demo Accounts

Running `flask seed-db` recreates the following demo users. All accounts
share the same password: **`password123`**.

| Email                | Username      |
|----------------------|---------------|
| alex@example.com     | alex_chen     |
| sarah@example.com    | sarah_kim     |
| film@example.com     | filmcritic99  |
| jordan@example.com   | jordan_lee    |
| maya@example.com     | maya_patel    |
| ghost@example.com    | ghost_user    |

> ⚠️ `flask seed-db` wipes existing data (users, movies, reviews,
> watchlist, follows, likes, comments) and recreates the demo dataset
> from scratch. It is intended for local development and testing only —
> do not run it against a database that has real data you want to keep.

---

## 🎞️ Movie Posters (OMDb)

Real movie posters are fetched from the [OMDb API](https://www.omdbapi.com/)
and cached as URLs in your local database.

- Sign up for a free OMDb API key and add it to your `.env`:
  ```env
  OMDB_KEY=your-omdb-api-key
  ```
- Run the fetch command to populate poster URLs for every movie:
  ```bash
  flask fetch-posters
  ```
- After running `flask seed-db`, posters reset along with the rest of
  the demo data and movies fall back to placeholder images. Re-run
  `flask fetch-posters` to repopulate them.
- **Recommended first-run order:**
  ```bash
  flask db upgrade
  flask seed-db
  flask fetch-posters
  python run.py
  ```
- Skipping this step is fine — the app works with placeholder posters,
  it just looks nicer with the real ones.

---

## ⚙️ Useful Flask CLI Commands

| Command                 | What it does                                                |
|-------------------------|-------------------------------------------------------------|
| `flask run`             | Start the dev server (does not seed or reset any data)      |
| `flask db upgrade`      | Apply pending migrations                                    |
| `flask db migrate -m …` | Generate a new migration from model changes                 |
| `flask seed-db`         | Reset demo data and recreate sample users with demo passwords |
| `flask fetch-posters`   | Fetch missing movie posters from OMDb (requires `OMDB_KEY`) |

---

## 🧪 Running the Tests

### Unit tests (unittest)

The unit tests spin up the app against an isolated temporary SQLite
database, so they never touch `app/app.db` or your `.env`.

Run just the unit suite:
```bash
python -m unittest tests.test_unit -v
```

Or run **all** tests (unit + Selenium) via test discovery:
```bash
python -m unittest discover tests -v
```

You should see 10 unit tests pass in about 1–2 seconds. The suite
covers sign-up + login, search filters, review CRUD, watchlist add,
like toggle, and the follow-yourself guard.

### Selenium tests (end-to-end)

The Selenium suite drives a real headless Chrome browser through core
user flows (load home, search, login, signup, watchlist via AJAX, …).
It starts the Flask dev server itself in a subprocess, so you do not
need to start the app separately — but it does run against your dev
database, so seed it first:

```bash
flask seed-db
python -m unittest tests.test_selenium
```

Selenium 4 auto-downloads the matching ChromeDriver, so you only need
Chrome itself installed locally. To watch the browser instead of
running headless, comment out the `--headless=new` line in
`test_selenium.py`'s `setUp`.

---

## 🤝 Contributing

1. Fork or branch off `main` (`git checkout -b feature/your-feature`)
2. Make your changes and add tests where it makes sense
3. Run the unit tests locally before opening a PR
4. Commit and push your branch
5. Open a Pull Request against `main` and request a review

---

