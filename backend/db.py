import sqlite3
from contextlib import contextmanager

from backend import config


class Database:
    """Доступ к базе. Один объект на файл БД (singleton), чтобы не плодить копии."""

    _instances = {}

    def __new__(cls, path=None):
        path = str(path or config.DB_PATH)
        if path not in cls._instances:
            obj = super().__new__(cls)
            obj.path = path
            cls._instances[path] = obj
        return cls._instances[path]

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql, params=()):
        with self.connect() as conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid

    def one(self, sql, params=()):
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def all(self, sql, params=()):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_db():
    return Database()
