"""Создаёт базу данных: применяет все миграции из database/migrations по порядку.

Запуск:  python init_db.py
Чтобы создать БД только до первой версии (для практики 12):  python init_db.py --upto 1
"""
import argparse
import os
import sqlite3
from pathlib import Path

from backend import config
from backend.security import hash_password
from backend.themes import THEMES


def applied_versions(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    return {row[0] for row in conn.execute("SELECT version FROM schema_version")}


def run_migrations(db_path, upto=None, quiet=False):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    done = applied_versions(conn)
    files = sorted(config.MIGRATIONS_DIR.glob("*.sql"))
    for f in files:
        version = int(f.name.split("_")[0])
        if version in done or (upto and version > upto):
            continue
        if not quiet:
            print("применяю миграцию", f.name)
        conn.executescript(f.read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()
    conn.close()


def seed_dictionaries(db_path, theme_name):
    """Справочники для текущей темы и администратор из ТЗ."""
    theme = THEMES[theme_name]
    conn = sqlite3.connect(db_path)
    for name in theme["rooms"]:
        conn.execute("INSERT OR IGNORE INTO room (name) VALUES (?)", (name,))
    for name in theme["payments"]:
        conn.execute("INSERT OR IGNORE INTO payment_method (name) VALUES (?)", (name,))
    for status_id, name in theme.get("statuses", {}).items():
        conn.execute("UPDATE status SET name = ? WHERE id = ?", (name, status_id))
    exists = conn.execute("SELECT 1 FROM user WHERE login = 'Conf2027'").fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO user (login, password_hash, fio, email, phone, role) VALUES (?, ?, ?, ?, ?, 'admin')",
            ("Conf2027", hash_password("Demo77"), "Администратор Портала", "admin@conf.example", "8(900)-000-00-00"),
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--upto", type=int, default=None)
    parser.add_argument("--db", default=config.DB_PATH)
    args = parser.parse_args()
    run_migrations(args.db, args.upto)
    if not args.upto or args.upto >= 2:
        seed_dictionaries(args.db, os.environ.get("THEME", config.THEME))
    print("база готова:", args.db)
