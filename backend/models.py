from backend.db import get_db
from backend import validators as v
from backend.security import hash_password


class BaseModel:
    """Общий класс для моделей. Каждая модель сама проверяет данные и сохраняет себя."""

    def __init__(self, data=None):
        self.data = data or {}
        self.db = get_db()

    def validate(self):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError


class User(BaseModel):
    def validate(self):
        d = self.data
        errors = v.collect({
            "login": v.check_login(d.get("login")),
            "password": v.check_password(d.get("password")),
            "fio": v.check_fio(d.get("fio")),
            "phone": v.check_phone(d.get("phone")),
            "email": v.check_email(d.get("email")),
        })
        # уникальность проверяем отдельно, это запрос к базе
        if "login" not in errors and self.find_by_login(d["login"]):
            errors["login"] = "Такой логин уже занят"
        if "email" not in errors and self.db.one("SELECT id FROM user WHERE email = ?", (d["email"].lower(),)):
            errors["email"] = "Этот email уже зарегистрирован"
        return errors

    def save(self):
        d = self.data
        return self.db.execute(
            "INSERT INTO user (login, password_hash, fio, email, phone, role) VALUES (?, ?, ?, ?, ?, ?)",
            (d["login"], hash_password(d["password"]), d["fio"].strip(), d["email"].lower(),
             d["phone"], d.get("role", "user")),
        )

    @staticmethod
    def find_by_login(login):
        return get_db().one("SELECT * FROM user WHERE login = ?", (login,))

    @staticmethod
    def profile(user_id):
        """Данные личного кабинета: профиль и счётчики заявок."""
        db = get_db()
        info = db.one("SELECT id, login, fio, email, phone, role FROM user WHERE id = ?", (user_id,))
        info["total"] = db.one("SELECT COUNT(*) AS n FROM request WHERE user_id = ?", (user_id,))["n"]
        info["done"] = db.one("SELECT COUNT(*) AS n FROM request WHERE user_id = ? AND status_id = 3", (user_id,))["n"]
        info["reviews"] = db.one(
            "SELECT COUNT(*) AS n FROM review rv JOIN request r ON r.id = rv.request_id WHERE r.user_id = ?", (user_id,))["n"]
        return info

    @staticmethod
    def find_by_id(user_id):
        return get_db().one("SELECT id, login, fio, email, phone, role FROM user WHERE id = ?", (user_id,))


REQUEST_SELECT = """
    SELECT r.id, r.created_at, u.fio, u.login,
           e.name AS event_name, e.date, e.start_time, e.description,
           e.room_id, r.payment_method_id,
           rm.name AS room, pm.name AS payment, s.id AS status_id, s.name AS status,
           rv.id AS review_id, rv.text AS review_text, rv.rating AS review_rating
    FROM request r
    JOIN user u            ON u.id = r.user_id
    JOIN event e           ON e.id = r.event_id
    JOIN room rm           ON rm.id = e.room_id
    JOIN payment_method pm ON pm.id = r.payment_method_id
    JOIN status s          ON s.id = r.status_id
    LEFT JOIN review rv    ON rv.request_id = r.id
"""


class Request(BaseModel):
    def validate(self):
        d = self.data
        errors = v.collect({
            "event_name": v.check_event_name(d.get("event_name")),
            "date": v.check_date(d.get("date")),
            "start_time": v.check_time(d.get("start_time")),
        })
        if not self.db.one("SELECT id FROM room WHERE id = ?", (d.get("room_id"),)):
            errors["room_id"] = "Выберите помещение из списка"
        if not self.db.one("SELECT id FROM payment_method WHERE id = ?", (d.get("payment_method_id"),)):
            errors["payment_method_id"] = "Выберите способ оплаты из списка"
        if len(d.get("description") or "") > 1000:
            errors["description"] = "Описание не длиннее 1000 символов"
        return errors

    def save(self):
        """Создаёт мероприятие и заявку в одной транзакции."""
        d = self.data
        with self.db.connect() as conn:
            cur = conn.execute(
                "INSERT INTO event (name, date, start_time, room_id, description) VALUES (?, ?, ?, ?, ?)",
                (d["event_name"].strip(), d["date"], d["start_time"], d["room_id"], (d.get("description") or "").strip()),
            )
            event_id = cur.lastrowid
            cur = conn.execute(
                "INSERT INTO request (user_id, event_id, status_id, payment_method_id) VALUES (?, ?, 1, ?)",
                (d["user_id"], event_id, d["payment_method_id"]),
            )
            request_id = cur.lastrowid
            conn.execute(
                "INSERT INTO status_history (request_id, status_id, changed_by) VALUES (?, 1, ?)",
                (request_id, d["user_id"]),
            )
        return request_id

    @staticmethod
    def update(request_id, data):
        """Изменение заявки (пока она новая): обновляем мероприятие и способ оплаты."""
        db = get_db()
        with db.connect() as conn:
            row = conn.execute("SELECT event_id FROM request WHERE id = ?", (request_id,)).fetchone()
            conn.execute(
                "UPDATE event SET name = ?, date = ?, start_time = ?, room_id = ?, description = ? WHERE id = ?",
                (data["event_name"].strip(), data["date"], data["start_time"], data["room_id"],
                 (data.get("description") or "").strip(), row["event_id"]),
            )
            conn.execute("UPDATE request SET payment_method_id = ? WHERE id = ?", (data["payment_method_id"], request_id))

    @staticmethod
    def delete(request_id):
        """Удаляет заявку вместе с отзывом и мероприятием, на которое больше никто не ссылается."""
        db = get_db()
        with db.connect() as conn:
            row = conn.execute("SELECT event_id FROM request WHERE id = ?", (request_id,)).fetchone()
            conn.execute("DELETE FROM review WHERE request_id = ?", (request_id,))
            conn.execute("DELETE FROM request WHERE id = ?", (request_id,))   # журнал статусов удалится каскадом
            conn.execute(
                "DELETE FROM event WHERE id = ? AND NOT EXISTS (SELECT 1 FROM request WHERE event_id = ?)",
                (row["event_id"], row["event_id"]),
            )

    @staticmethod
    def for_user(user_id):
        sql = REQUEST_SELECT + " WHERE r.user_id = ? ORDER BY r.id DESC"
        return get_db().all(sql, (user_id,))

    @staticmethod
    def find(request_id):
        return get_db().one(REQUEST_SELECT + " WHERE r.id = ?", (request_id,))

    @staticmethod
    def search(status_id=None, room_id=None, date=None, text=None):
        """Список заявок для админа с фильтрами."""
        where, params = [], []
        if status_id:
            where.append("r.status_id = ?")
            params.append(status_id)
        if room_id:
            where.append("e.room_id = ?")
            params.append(room_id)
        if date:
            where.append("e.date = ?")
            params.append(date)
        if text:
            where.append("(e.name LIKE ? OR u.fio LIKE ?)")
            params += ["%" + text + "%", "%" + text + "%"]
        sql = REQUEST_SELECT
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY r.id DESC"
        return get_db().all(sql, params)

    @staticmethod
    def set_status(request_id, status_id, admin_id):
        db = get_db()
        with db.connect() as conn:
            conn.execute("UPDATE request SET status_id = ? WHERE id = ?", (status_id, request_id))
            conn.execute(
                "INSERT INTO status_history (request_id, status_id, changed_by) VALUES (?, ?, ?)",
                (request_id, status_id, admin_id),
            )


class Review(BaseModel):
    def validate(self):
        d = self.data
        errors = v.collect({
            "text": v.check_review_text(d.get("text")),
            "rating": v.check_rating(d.get("rating")),
        })
        req = Request.find(d.get("request_id"))
        # отзыв только на свою заявку, только после завершения и только один раз
        if not req or req["login"] != d.get("login"):
            errors["request"] = "Заявка не найдена"
        elif req["status_id"] != 3:
            errors["request"] = "Отзыв можно оставить только после завершения мероприятия"
        elif req["review_id"]:
            errors["request"] = "Вы уже оставили отзыв на эту заявку"
        return errors

    def save(self):
        d = self.data
        return self.db.execute(
            "INSERT INTO review (request_id, text, rating) VALUES (?, ?, ?)",
            (d["request_id"], d["text"].strip(), int(d["rating"])),
        )


def dictionaries():
    """Справочники для выпадающих списков."""
    db = get_db()
    return {
        "rooms": db.all("SELECT id, name FROM room ORDER BY id"),
        "payments": db.all("SELECT id, name FROM payment_method ORDER BY id"),
        "statuses": db.all("SELECT id, name FROM status ORDER BY id"),
    }
