"""Воспроизводит ошибку из практики 5.

Две регистрации с одним логином приходят почти одновременно: обе проходят validate()
(логина в базе ещё нет), а при сохранении вторая падает на UNIQUE.
Здесь validate() второго запроса подменяем, чтобы получить такую же ситуацию.
"""
import os
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import init_db
from backend import config
from backend.models import User

fd, path = tempfile.mkstemp(suffix=".db")
os.close(fd)
os.remove(path)
config.DB_PATH = path
init_db.run_migrations(path, quiet=True)
init_db.seed_dictionaries(path, "conference")

from app import create_app

app = create_app()
client = app.test_client()
client.get("/login")
with client.session_transaction() as s:
    token = s["csrf"]

data = {"login": "double_user", "password": "Password123", "fio": "Петров Пётр Петрович",
        "phone": "8(900)-111-22-33", "email": "double@example.ru"}

first = client.post("/api/register", json=data, headers={"X-CSRF-Token": token})
print("первая регистрация:", first.status_code)

data["email"] = "double2@example.ru"
with mock.patch.object(User, "validate", return_value={}):
    second = client.post("/api/register", json=data, headers={"X-CSRF-Token": token})
print("вторая регистрация (тот же логин):", second.status_code)
print("тело ответа:", second.get_data(as_text=True)[:90].replace("\n", " "))
