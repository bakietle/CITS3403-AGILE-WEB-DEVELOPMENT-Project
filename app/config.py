import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY_VALUE = os.environ.get("SECRET_KEY")
if not SECRET_KEY_VALUE:
    raise RuntimeError(
        "SECRET_KEY is not set. Create a .env file in the project root with "
        "SECRET_KEY set to a secure value."
    )

DATABASE_URL = os.environ.get("DATABASE_URL") or (
    f"sqlite:///{(Path(__file__).resolve().parent / 'app.db').as_posix()}"
)


class Config:
    SECRET_KEY = SECRET_KEY_VALUE
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
