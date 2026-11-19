"""Application settings loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # Put a generated key in the ignored local .env file.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'campus_lost_found.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MATCH_WEIGHTS = {
        "name": 30,
        "description": 25,
        "category": 15,
        "colour": 10,
        "location": 10,
        "date": 10,
    }
    MATCH_MIN_SCORE = 50
    MATCH_POSSIBLE_SCORE = 70
    MATCH_STRONG_SCORE = 90
    MATCH_DATE_WINDOW_DAYS = 30
