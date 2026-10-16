import os
import tempfile

import init_db
from backend import config


def make_app(theme="conference"):
    """Создаёт приложение с отдельной временной базой, чтобы тесты не трогали рабочую."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    config.DB_PATH = path
    init_db.run_migrations(path, quiet=True)
    init_db.seed_dictionaries(path, theme)
    from app import create_app
    app = create_app({"TESTING": True, "THEME": theme})
    return app, path


def get_token(client):
    """Открываем любую страницу, чтобы в сессии появился CSRF-токен, и забираем его."""
    client.get("/login")
    with client.session_transaction() as s:
        return s["csrf"]


def post_json(client, url, data, token=None):
    headers = {}
    if token is not None:
        headers["X-CSRF-Token"] = token
    return client.post(url, json=data, headers=headers)


USER = {"login": "student01", "password": "Password123", "fio": "Иванов Иван Иванович",
        "phone": "8(900)-123-45-67", "email": "ivanov@example.ru"}


def register_and_login(client, data=None):
    data = data or USER
    token = get_token(client)
    post_json(client, "/api/register", data, token)
    r = post_json(client, "/api/login", {"login": data["login"], "password": data["password"]}, token)
    # при входе сессия пересоздаётся, поэтому токен нужен новый
    client.get("/dashboard")
    with client.session_transaction() as s:
        return s["csrf"], r


def login_admin(client):
    token = get_token(client)
    r = post_json(client, "/api/login", {"login": "Conf2027", "password": "Demo77"}, token)
    client.get("/admin")
    with client.session_transaction() as s:
        return s["csrf"], r
