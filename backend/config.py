import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("DATABASE", str(BASE_DIR / "database" / "conference.db"))
MIGRATIONS_DIR = BASE_DIR / "database" / "migrations"


def get_secret_key():
    """Ключ для подписи сессий. Берём из окружения, иначе создаём файл при первом запуске."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    secret_file = BASE_DIR / "database" / ".secret"
    if not secret_file.exists():
        secret_file.parent.mkdir(exist_ok=True)
        secret_file.write_text(secrets.token_hex(32))
    return secret_file.read_text().strip()


# какая тематика сайта включена (практика 17), по умолчанию конференции
THEME = os.environ.get("THEME", "conference")
