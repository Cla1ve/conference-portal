"""Создаёт БД версии 1 с данными (как была до доработки), чтобы показать миграцию на версию 2.

Запуск:  python tools/make_v1_demo.py путь/к/файлу.db
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.security import hash_password
import init_db

path = sys.argv[1]
if os.path.exists(path):
    os.remove(path)
init_db.run_migrations(path, upto=1, quiet=True)

conn = sqlite3.connect(path)
conn.execute("PRAGMA foreign_keys = ON")
users = [("Conf2027", "Demo77", "Администратор Портала", "admin@conf.example", "8(900)-000-00-00", "admin"),
         ("elmurat2027", "Student2027", "Маматисаков Элмурат Сапарбекович", "elmurat@example.ru", "8(915)-204-18-36", "user"),
         ("anna_ivanova", "Password123", "Иванова Анна Сергеевна", "anna@example.ru", "8(903)-555-12-90", "user")]
for login, pwd, fio, email, phone, role in users:
    conn.execute("INSERT INTO user (login, password_hash, fio, email, phone, role) VALUES (?,?,?,?,?,?)", (login, hash_password(pwd), fio, email, phone, role))

events = [("Хакатон студентов", "2026-10-28", "10:00", "Аудитория", "Мини-проекты"), ("Кинопоказ", "2026-10-31", "19:00", "Кинозал", ""),
          ("Встреча клуба Python", "2026-11-05", "18:30", "Коворкинг", ""), ("Защита курсовых", "2026-11-15", "09:00", "Аудитория", ""),
          ("Мастер-класс по Figma", "2026-11-10", "14:00", "Коворкинг", "")]
for e in events:
    conn.execute("INSERT INTO event (name, date, start_time, place, description) VALUES (?,?,?,?,?)", e)

requests = [(2, 1, 3, "При очном посещении"), (3, 2, 3, "СБП"), (2, 3, 2, "СБП"), (2, 4, 1, "При очном посещении"), (3, 5, 2, "При очном посещении")]
for r in requests:
    conn.execute("INSERT INTO request (user_id, event_id, status_id, payment_method) VALUES (?,?,?,?)", r)
conn.execute("INSERT INTO review (request_id, text, rating) VALUES (1, 'Всё хорошо', 5)")
conn.execute("INSERT INTO review (request_id, text, rating) VALUES (2, 'Было прохладно', 4)")
conn.commit()
for t in ("user", "event", "request", "review"):
    print(t, conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0])
conn.close()
