from flask import Blueprint, render_template, request, jsonify, g

from backend.models import Request, dictionaries
from backend.security import login_required

admin_bp = Blueprint("admin", __name__)


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@admin_bp.get("/admin")
@login_required("admin")
def admin_page():
    return render_template("admin.html", **dictionaries())


@admin_bp.get("/api/admin/requests")
@login_required("admin")
def list_requests():
    items = Request.search(
        status_id=to_int(request.args.get("status")),
        room_id=to_int(request.args.get("room")),
        date=request.args.get("date") or None,
        text=(request.args.get("q") or "").strip() or None,
    )
    return jsonify(success=True, items=items)


@admin_bp.post("/api/admin/requests/<int:request_id>/status")
@login_required("admin")
def change_status(request_id):
    data = request.get_json(silent=True) or {}
    new_status = to_int(data.get("status_id"))
    current = Request.find(request_id)
    if not current:
        return jsonify(success=False, message="Заявка не найдена"), 404
    # статусы идут только вперёд: Новая -> Назначено -> Завершено
    if new_status != current["status_id"] + 1 or new_status > 3:
        return jsonify(success=False, message="Нельзя изменить статус на выбранный"), 400
    Request.set_status(request_id, new_status, g.user["id"])
    return jsonify(success=True, item=Request.find(request_id))
