# CITS3403-AGILE-WEB-DEVELOPMENT-Project

# 🌟 Movie Star

> A web application where users can discover, rate, and review movies.

---

## 📖 About

**Movie Star** is a community-driven movie rating platform that lets users sign up, log in, and share their thoughts on their favourite films. Whether you loved it or hated it — your rating counts.

---

## ✨ Features

- 🔐 **User Authentication** — Secure sign up and login system
- ⭐ **Rate & Review Movies** — Submit ratings and written reviews for any movie
- 🎬 More features coming soon...

---

## 🛠️ Tech Stack

| Layer      | Technology          |
|------------|---------------------|
| Frontend   | HTML, Tailwind CSS, Bootstrap |
| Backend    | Python + Flask      |
| Database   | TBD                 |

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- [Python 3.8+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/)
- [Git](https://git-scm.com/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/movie-star.git
   cd movie-star
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Development database commands

- `python run.py` or `flask run` starts the app and should not reset data.
- `flask db upgrade` applies database migrations without reseeding demo data.
- `flask seed-db` intentionally resets and recreates demo data. This recreates demo users, so changed demo passwords are reset to the seed password values.

5. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key_here
   DATABASE_URL=your_database_url_here
   ```

6. **Run the application**
   ```bash
   flask run
   ```

7. Open your browser and go to `http://localhost:5000`

---

## 📁 Project Structure

```
movie-forum/
├─ frontend/
│  ├─ __init__.py
│  ├─ routes.py
│  ├─ models.py
│  ├─ forms.py
│  ├─ templates/ --HTMl pages goes here--
│  └─ static/
│     ├─ css/ --CSS pages goes here--
│     ├─ js/

├─ migrations/
├─ config.py
├─ run.py
└─ requirements.txt
```

---

## 👥 Team

| Name | Role |
|------|------|
| TBD  | TBD  |

---

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📬 Contact

Have questions or suggestions? Open an issue on the repository.

---

*Movie Star — Because every opinion deserves a stage.* 🎬

