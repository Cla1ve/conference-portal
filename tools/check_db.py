"""Проверка целостности БД после миграции.   Запуск:  python tools/check_db.py путь/к/файлу.db"""
import sqlite3
import sys

path = sys.argv[1]
conn = sqlite3.connect(path)
conn.execute("PRAGMA foreign_keys = ON")

print("версия схемы:", conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0])
print("таблицы:", ", ".join(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")))
print()
print("записей в таблицах:")
for t in ("user", "room", "payment_method", "status", "event", "request", "review", "status_history"):
    print("  %-15s %d" % (t, conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]))
print()
fk = conn.execute("PRAGMA foreign_key_check").fetchall()
print("foreign_key_check:", "нарушений нет" if not fk else fk)
print("integrity_check:", conn.execute("PRAGMA integrity_check").fetchone()[0])

checks = {
    "мероприятий без помещения": "SELECT COUNT(*) FROM event WHERE room_id IS NULL",
    "заявок без способа оплаты": "SELECT COUNT(*) FROM request WHERE payment_method_id IS NULL",
    "заявок без записи в журнале": "SELECT COUNT(*) FROM request r WHERE NOT EXISTS (SELECT 1 FROM status_history h WHERE h.request_id = r.id)",
}
print()
for title, sql in checks.items():
    print("%-30s %d" % (title + ":", conn.execute(sql).fetchone()[0]))
conn.close()
