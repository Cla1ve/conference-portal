import os
import time
from datetime import timedelta
from pathlib import Path

from flask import Flask, session, request, g, jsonify, render_template, url_for

from backend import config
from backend.db import get_db
from backend.security import csrf_token, check_csrf
from backend.themes import THEMES


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )
    app.config.update(
        SECRET_KEY=config.get_secret_key(),
        SESSION_COOKIE_NAME="conf_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=32 * 1024,
        THEME=os.environ.get("THEME", config.THEME),
        USE_MIN=os.environ.get("USE_MIN", "1") != "0",
    )
    if test_config:
        app.config.update(test_config)
    app.json.ensure_ascii = False

    @app.before_request
    def load_user():
        g.user = None
        user_id = session.get("user_id")
        if user_id:
            # сессия живёт 30 минут с последнего действия
            if time.time() - session.get("last_seen", 0) > 30 * 60:
                session.clear()
            else:
                g.user = get_db().one("SELECT id, login, fio, role FROM user WHERE id = ?", (user_id,))
                if g.user is None:
                    session.clear()
                else:
                    session["last_seen"] = time.time()
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and not check_csrf():
            return jsonify(success=False, message="Страница устарела, обновите её и повторите"), 400

    static_dir = Path(app.static_folder)

    def asset(path):
        """Адрес css/js файла: минифицированный из static/dist, если он есть, иначе исходный.
        В конце ?v= с временем изменения файла, чтобы браузер брал свежую версию."""
        name, ext = path.rsplit(".", 1)
        small = "dist/" + name.split("/")[-1] + ".min." + ext
        # если исходник правили после сборки, берём исходник, а не устаревший min-файл
        if app.config["USE_MIN"] and (static_dir / small).exists()                 and (static_dir / small).stat().st_mtime >= (static_dir / path).stat().st_mtime:
            path = small
        return url_for("static", filename=path, v=int((static_dir / path).stat().st_mtime))

    @app.context_processor
    def inject_globals():
        theme = THEMES.get(app.config["THEME"], THEMES["conference"])
        return {"theme": theme, "csrf_token": csrf_token, "user": g.get("user"), "asset": asset}

    @app.after_request
    def add_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=3600"
        else:
            response.headers["Cache-Control"] = "no-store"
        return response

    from backend.routes.pages import pages_bp
    from backend.routes.auth import auth_bp
    from backend.routes.requests import requests_bp
    from backend.routes.admin import admin_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify(success=False, message="Не найдено"), 404
        return render_template("error.html", code=404, text="Такой страницы нет"), 404

    @app.errorhandler(500)
    def server_error(error):
        # пользователю показываем понятный текст, подробности остаются в логе сервера
        if request.path.startswith("/api/"):
            return jsonify(success=False, message="Ошибка на сервере, попробуйте позже"), 500
        return render_template("error.html", code=500, text="Что-то пошло не так"), 500

    @app.errorhandler(413)
    def too_big(error):
        return jsonify(success=False, message="Слишком большой запрос"), 413

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    create_app().run(host="127.0.0.1", port=port, debug=False)
