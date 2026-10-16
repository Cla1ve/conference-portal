import time

from flask import Blueprint, render_template, request, jsonify, session, redirect, g

from backend.models import User
from backend.security import verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    if g.user:
        return redirect("/home")
    return render_template("login.html")


@auth_bp.get("/register")
def register_page():
    if g.user:
        return redirect("/home")
    return render_template("register.html")


@auth_bp.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    user = User(data)
    errors = user.validate()
    if errors:
        return jsonify(success=False, message="Проверьте поля формы", errors=errors), 400
    user.save()
    return jsonify(success=True, message="Регистрация прошла успешно"), 201


@auth_bp.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    found = User.find_by_login(data.get("login", ""))
    # сообщение одинаковое и для неверного логина, и для неверного пароля
    if not found or not verify_password(data.get("password", ""), found["password_hash"]):
        return jsonify(success=False, message="Неверный логин или пароль"), 401
    session.clear()
    session["user_id"] = found["id"]
    session["last_seen"] = time.time()
    session.permanent = True
    target = "/admin" if found["role"] == "admin" else "/dashboard"
    return jsonify(success=True, redirect=target)


@auth_bp.post("/api/logout")
def logout():
    session.clear()
    return jsonify(success=True, redirect="/login")
