from pathlib import Path


class Config:
    SECRET_KEY = "dev-secret-key"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(Path(__file__).resolve().parent / 'app.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
