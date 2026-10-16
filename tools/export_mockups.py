"""Собирает статические html-макеты страниц из шаблонов сайта (без сервера и без базы).

Запуск:  python tools/export_mockups.py
Папка design/desktop для компьютера, design/mobile для телефона 390x844.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import render_template
from app import create_app
from backend.themes import THEMES

ROOMS = [{"id": 1, "name": "Аудитория"}, {"id": 2, "name": "Коворкинг"}, {"id": 3, "name": "Кинозал"}]
PAYMENTS = [{"id": 1, "name": "При очном посещении"}, {"id": 2, "name": "СБП"}]
STATUSES = [{"id": 1, "name": "Новая"}, {"id": 2, "name": "Мероприятие назначено"}, {"id": 3, "name": "Завершено"}]

EVENTS = [
    {"name": "Хакатон студентов колледжа", "date": "2026-10-28", "start_time": "10:00", "room": "Аудитория", "description": "Командная разработка мини-проектов, 40 человек"},
    {"name": "Кинопоказ документального фильма", "date": "2026-10-31", "start_time": "19:00", "room": "Кинозал", "description": "Показ и обсуждение, до 60 мест"},
    {"name": "Встреча клуба Python", "date": "2026-11-05", "start_time": "18:30", "room": "Коворкинг", "description": "Разбор задач, обмен опытом"},
]

REQUESTS = [
    {"id": 3, "event_name": "Защита курсовых проектов", "date": "2026-11-15", "start_time": "09:00", "room": "Аудитория", "payment": "При очном посещении", "status_id": 1, "status": "Новая", "review_id": None},
    {"id": 2, "event_name": "Встреча клуба Python", "date": "2026-11-05", "start_time": "18:30", "room": "Коворкинг", "payment": "СБП", "status_id": 2, "status": "Мероприятие назначено", "review_id": None},
    {"id": 1, "event_name": "Хакатон студентов колледжа", "date": "2026-10-28", "start_time": "10:00", "room": "Аудитория", "payment": "При очном посещении", "status_id": 3, "status": "Завершено", "review_id": 1, "review_rating": 5, "review_text": "Помещение удобное, всё работало. Спасибо!"},
]

USER = {"id": 1, "login": "elmurat2027", "fio": "Маматисаков Элмурат Сапарбекович", "role": "user"}
ADMIN = {"id": 2, "login": "Conf2027", "fio": "Администратор Портала", "role": "admin"}

LINKS = {"/login": "login.html", "/register": "register.html", "/dashboard": "dashboard.html", "/request/new": "request_new.html",
         "/admin": "admin.html", "/profile": "profile.html", "/": "index.html"}


def admin_cards():
    """Карточки заявок для макета панели администратора (на сайте их рисует admin.js)."""
    items = [
        (8, 1, "Новая", "Научная конференция студентов", "Маматисаков Элмурат (elmurat2027)", "2026-12-05, 11:30", "Аудитория", "СБП", "Назначить мероприятие"),
        (5, 2, "Мероприятие назначено", "Мастер-класс по дизайну интерфейсов", "Иванова Анна (anna_ivanova)", "2026-11-10, 14:00", "Коворкинг", "При очном посещении", "Завершить"),
        (4, 3, "Завершено", "Кинопоказ документального фильма", "Иванова Анна (anna_ivanova)", "2026-10-31, 19:00", "Кинозал", "СБП", None),
    ]
    html = ['<div class="cards" id="admin-cards">']
    for n, sid, st, title, who, when, room, pay, btn in items:
        html.append(f'<article class="card"><div class="card-top"><span class="status status-{sid}">{st}</span><span class="muted">№ {n}</span></div>'
                    f'<h3>{title}</h3><div class="user-line">{who}</div><dl class="meta">'
                    f'<div><dt>Дата</dt><dd>{when}</dd></div><div><dt>Помещение</dt><dd>{room}</dd></div><div><dt>Оплата</dt><dd>{pay}</dd></div></dl>'
                    + (f'<div class="card-actions"><button class="btn btn-small" type="button">{btn}</button></div>' if btn else "") + "</article>")
    html.append("</div>")
    return "".join(html)


def fix_links(html, depth_to_root, mobile):
    prefix = "../" * depth_to_root
    html = html.replace('href="/static/', f'href="{prefix}frontend/static/').replace('src="/static/', f'src="{prefix}frontend/static/')
    html = html.replace('srcset="/static/', f'srcset="{prefix}frontend/static/')
    html = html.replace('href="/theme.css"', 'href="../theme.css"')
    html = re.sub(r'<script src="[^"]+"></script>', "", html)          # в макете скрипты не нужны
    for url, name in LINKS.items():
        html = html.replace(f'href="{url}"', f'href="{name}"')
    html = html.replace('<meta name="csrf-token"', '<meta name="generator" content="export_mockups.py"')
    return html


def main():
    app = create_app({"TESTING": True})
    out_root = ROOT / "design"
    (out_root).mkdir(exist_ok=True)
    theme = THEMES["conference"]
    (out_root / "theme.css").write_text(":root {\n  --primary: %s;\n  --accent: %s;\n}\n" % (theme["primary"], theme["accent"]), encoding="utf-8")

    pages = {
        "index.html": ("index.html", {"events": EVENTS, "user": None}),
        "login.html": ("login.html", {"user": None}),
        "register.html": ("register.html", {"user": None}),
        "dashboard.html": ("dashboard.html", {"requests": REQUESTS, "user": USER}),
        "request_new.html": ("request_new.html", {"rooms": ROOMS, "payments": PAYMENTS, "user": USER}),
        "admin.html": ("admin.html", {"rooms": ROOMS, "statuses": STATUSES, "user": ADMIN}),
        "profile.html": ("profile.html", {"user": USER, "profile": {"login": "elmurat2027", "fio": "Маматисаков Элмурат Сапарбекович", "email": "elmurat@example.ru", "phone": "8(915)-204-18-36", "total": 3, "done": 1, "reviews": 1}}),
    }
    for kind in ("desktop", "mobile"):
        folder = out_root / kind
        folder.mkdir(exist_ok=True)
        for name, (tpl, ctx) in pages.items():
            with app.test_request_context("/"):
                html = render_template(tpl, **ctx)
            html = fix_links(html, 2, kind == "mobile")
            if name == "admin.html":
                html = html.replace('<div class="cards" id="admin-cards" aria-live="polite"></div>', admin_cards())
                html = html.replace('<span class="muted" id="counter"></span>', '<span class="muted" id="counter">Найдено: 3</span>')
            if kind == "mobile":
                html = html.replace("</head>", '    <link rel="stylesheet" href="mobile.css">\n</head>')
            (folder / name).write_text(html, encoding="utf-8")
    (out_root / "mobile" / "mobile.css").write_text(
        "/* макет для экрана 390x844: на компьютере показываем в рамке телефона */\n"
        "@media (min-width: 500px) {\n  body { max-width: 390px; margin: 0 auto; border-left: 1px solid #ccd; border-right: 1px solid #ccd; box-shadow: 0 0 30px rgba(0,0,0,.15); }\n}\n",
        encoding="utf-8")
    print("макеты сохранены в", out_root)


if __name__ == "__main__":
    main()
