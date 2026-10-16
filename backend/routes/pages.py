from flask import Blueprint, render_template, g, redirect, current_app, url_for

from backend.db import get_db
from backend.themes import THEMES

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def index():
    # гостю показываем ближайшие подтверждённые мероприятия
    events = get_db().all(
        """
        SELECT e.name, e.date, e.start_time, e.description, rm.name AS room
        FROM request r
        JOIN event e ON e.id = r.event_id
        JOIN room rm ON rm.id = e.room_id
        WHERE r.status_id IN (2, 3)
        ORDER BY e.date, e.start_time
        LIMIT 12
        """
    )
    return render_template("index.html", events=events)


@pages_bp.get("/favicon.ico")
def favicon():
    """Некоторые браузеры всё равно просят /favicon.ico, отправляем их к значку темы."""
    theme = THEMES.get(current_app.config["THEME"], THEMES["conference"])
    return redirect(url_for("static", filename="img/" + theme["logo"]), code=302)


@pages_bp.get("/theme.css")
def theme_css():
    """Цвета текущей темы отдаём как css-переменные (inline style запрещён политикой CSP)."""
    from flask import current_app, Response
    from backend.themes import THEMES
    theme = THEMES.get(current_app.config["THEME"], THEMES["conference"])
    css = ":root {\n  --primary: %s;\n  --accent: %s;\n  --bg: %s;\n}\n" % (theme["primary"], theme["accent"], theme["bg"])
    return Response(css, mimetype="text/css")


@pages_bp.get("/home")
def home():
    if g.user and g.user["role"] == "admin":
        return redirect("/admin")
    if g.user:
        return redirect("/dashboard")
    return redirect("/login")
