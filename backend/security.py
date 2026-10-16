import hmac
import secrets
from functools import wraps

from flask import session, request, jsonify, redirect, g
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


def check_csrf():
    """Для POST-запросов токен должен прийти в заголовке X-CSRF-Token."""
    expected = session.get("csrf", "")
    got = request.headers.get("X-CSRF-Token", "")
    return bool(expected) and hmac.compare_digest(expected, got)


def login_required(role=None):
    """Проверка входа и роли. Для страниц редирект, для API ответ JSON с кодом."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_api = request.path.startswith("/api/")
            if g.user is None:
                if is_api:
                    return jsonify(success=False, message="Нужно войти в систему"), 401
                return redirect("/login")
            if role and g.user["role"] != role:
                if is_api:
                    return jsonify(success=False, message="Недостаточно прав"), 403
                return "Доступ запрещён", 403
            return func(*args, **kwargs)

        return wrapper

    return decorator
