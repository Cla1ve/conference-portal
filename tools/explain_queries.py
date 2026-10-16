"""Планы выполнения основных запросов и их время на большой базе.

Запуск:  python tools/explain_queries.py [--upto N]
Создаёт временную базу, заполняет её тестовыми данными (20 000 заявок) и для каждого запроса
печатает план (EXPLAIN QUERY PLAN) и среднее время. --upto 2 покажет базу без новых индексов.
"""
import argparse
import os
import random
import sqlite3
import sys
import tempfile
import time
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
parser = argparse.ArgumentParser()
parser.add_argument("--upto", type=int, default=None)
args = parser.parse_args()

db_file = os.path.join(tempfile.mkdtemp(), "explain.db")
import init_db  # noqa: E402
from backend.models import REQUEST_SELECT  # noqa: E402

init_db.run_migrations(db_file, upto=args.upto, quiet=True)
init_db.seed_dictionaries(db_file, "conference")
conn = sqlite3.connect(db_file)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

random.seed(1)
conn.executemany(
    "INSERT INTO user (login, password_hash, fio, email, phone) VALUES (?, 'x', ?, ?, '8(900)-000-00-00')",
    [(f"user{i:05d}", f"Тестов Тест{i}", f"user{i}@example.ru") for i in range(1, 501)])
rooms = [r[0] for r in conn.execute("SELECT id FROM room")]
pays = [r[0] for r in conn.execute("SELECT id FROM payment_method")]
base = date(2026, 1, 1)
for i in range(1, 20001):
    cur = conn.execute("INSERT INTO event (name, date, start_time, room_id, description) VALUES (?, ?, '10:00', ?, '')",
                       (f"Мероприятие {i}", (base + timedelta(days=random.randint(0, 700))).isoformat(), random.choice(rooms)))
    conn.execute("INSERT INTO request (user_id, event_id, payment_method_id, status_id) VALUES (?, ?, ?, ?)",
                 (random.randint(2, 501), cur.lastrowid, random.choice(pays), random.randint(1, 3)))
conn.commit()
conn.execute("ANALYZE")

QUERIES = [
    ("заявки одного пользователя", REQUEST_SELECT + " WHERE r.user_id = ? ORDER BY r.id DESC", (250,)),
    ("админ: фильтр по дате", REQUEST_SELECT + " WHERE e.date = ? ORDER BY r.id DESC", ("2026-06-15",)),
    ("админ: статус и помещение", REQUEST_SELECT + " WHERE r.status_id = ? AND e.room_id = ? ORDER BY r.id DESC", (2, 1)),
    ("есть ли заявки на мероприятие (при удалении)", "SELECT 1 FROM request WHERE event_id = ?", (777,)),
    ("счётчики кабинета", "SELECT COUNT(r.id), SUM(r.status_id = 3), COUNT(rv.id) FROM request r "
                          "LEFT JOIN review rv ON rv.request_id = r.id WHERE r.user_id = ?", (250,)),
]
print("версия схемы:", conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0], "| заявок:", 20000)
for title, sql, params in QUERIES:
    plan = [r["detail"] for r in conn.execute("EXPLAIN QUERY PLAN " + sql, params)]
    start = time.perf_counter()
    for _ in range(50):
        conn.execute(sql, params).fetchall()
    ms = (time.perf_counter() - start) / 50 * 1000
    print(f"\n{title}: {ms:.2f} мс")
    for line in plan[:3]:
        print("   ", line)
