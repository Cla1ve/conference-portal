from flask import Blueprint, render_template, request, jsonify, g

from backend.models import Request, Review, User, dictionaries
from backend.security import login_required

requests_bp = Blueprint("requests", __name__)


@requests_bp.get("/dashboard")
@login_required("user")
def dashboard():
    return render_template("dashboard.html", requests=Request.for_user(g.user["id"]))


@requests_bp.get("/profile")
@login_required("user")
def profile():
    return render_template("profile.html", profile=User.profile(g.user["id"]))


@requests_bp.get("/request/new")
@login_required("user")
def new_request_page():
    return render_template("request_new.html", **dictionaries())


@requests_bp.get("/request/<int:request_id>/edit")
@login_required("user")
def edit_request_page(request_id):
    item = Request.find(request_id)
    if not item or item["login"] != g.user["login"] or item["status_id"] != 1:
        return render_template("error.html", code=404, text="Заявку нельзя изменить"), 404
    return render_template("request_new.html", edit=item, **dictionaries())


def own_new_request(request_id):
    """Заявка пользователя, которую ещё можно менять или отменять (статус Новая)."""
    item = Request.find(request_id)
    if not item or item["login"] != g.user["login"]:
        return None, (jsonify(success=False, message="Заявка не найдена"), 404)
    if item["status_id"] != 1:
        return None, (jsonify(success=False, message="Заявка уже обработана, изменить её нельзя"), 400)
    return item, None


@requests_bp.put("/api/requests/<int:request_id>")
@login_required("user")
def update_request(request_id):
    item, error = own_new_request(request_id)
    if error:
        return error
    data = request.get_json(silent=True) or {}
    req = Request(data)
    errors = req.validate()
    if errors:
        return jsonify(success=False, message="Проверьте поля формы", errors=errors), 400
    Request.update(request_id, data)
    return jsonify(success=True, redirect="/dashboard")


@requests_bp.delete("/api/requests/<int:request_id>")
@login_required("user")
def cancel_request(request_id):
    item, error = own_new_request(request_id)
    if error:
        return error
    Request.delete(request_id)
    return jsonify(success=True)


@requests_bp.post("/api/requests")
@login_required("user")
def create_request():
    data = request.get_json(silent=True) or {}
    data["user_id"] = g.user["id"]
    req = Request(data)
    errors = req.validate()
    if errors:
        return jsonify(success=False, message="Проверьте поля формы", errors=errors), 400
    req_id = req.save()
    return jsonify(success=True, id=req_id, redirect="/dashboard"), 201


@requests_bp.post("/api/requests/<int:request_id>/review")
@login_required("user")
def add_review(request_id):
    data = request.get_json(silent=True) or {}
    data["request_id"] = request_id
    data["login"] = g.user["login"]
    review = Review(data)
    errors = review.validate()
    if errors:
        return jsonify(success=False, message=next(iter(errors.values())), errors=errors), 400
    review.save()
    return jsonify(success=True, message="Спасибо за отзыв!"), 201
