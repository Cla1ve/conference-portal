"""Воспроизведение дефектов BR-002 и BR-003 прямыми запросами к API (мимо формы в браузере).

Запуск: python tools/repro_defects.py
"""
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
db_file = os.path.join(tempfile.mkdtemp(), "repro.db")
os.environ["DATABASE"] = db_file
os.environ["SECRET_KEY"] = "repro"

import init_db  # noqa: E402

init_db.run_migrations(db_file, quiet=True)
init_db.seed_dictionaries(db_file, "conference")
from app import create_app  # noqa: E402

client = create_app().test_client()


def csrf(url):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


print("BR-002: регистрация с паролем из 8 пробелов")
r = client.post("/api/register", headers={"X-CSRF-Token": csrf("/register")}, json={
    "login": "space_pass1", "password": " " * 8, "fio": "Иванов Иван",
    "phone": "8(900)-111-22-33", "email": "sp1@example.ru"})
print("  ответ:", r.status_code, r.get_json())

# для второй проверки нужен обычный пользователь
client.post("/api/register", headers={"X-CSRF-Token": csrf("/register")}, json={
    "login": "repro_user1", "password": "Password123", "fio": "Петров Пётр",
    "phone": "8(900)-111-22-34", "email": "repro1@example.ru"})
client.post("/api/login", headers={"X-CSRF-Token": csrf("/login")}, json={"login": "repro_user1", "password": "Password123"})
print("BR-003: заявка на сегодня со временем, которое уже прошло")
past = (datetime.now() - timedelta(hours=3)).strftime("%H:%M")
if datetime.now().hour < 3:
    past = "00:00"
r = client.post("/api/requests", headers={"X-CSRF-Token": csrf("/request/new")}, json={
    "event_name": "Конференция по тестированию", "date": date.today().isoformat(),
    "start_time": past, "room_id": 1, "payment_method_id": 1, "description": ""})
print("  сейчас", datetime.now().strftime("%H:%M"), "время в заявке", past)
print("  ответ:", r.status_code, r.get_json())
