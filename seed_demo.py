"""Тестовые данные для показа и скриншотов.  Запуск: python seed_demo.py"""
from datetime import date, timedelta

from backend.db import get_db
from backend.models import User, Request, Review

USERS = [
    ("elmurat2027", "Student2027", "Маматисаков Элмурат Сапарбекович", "elmurat@example.ru", "8(915)-204-18-36"),
    ("anna_ivanova", "Password123", "Иванова Анна Сергеевна", "anna.ivanova@example.ru", "8(903)-555-12-90"),
    ("petrov_pavel", "Password123", "Петров Павел Игоревич", "petrov@example.ru", "8(926)-777-45-02"),
]

# (логин, название, дней от сегодня, время, помещение, оплата, описание, до какого статуса довести)
REQUESTS = [
    ("elmurat2027", "Хакатон студентов колледжа", 12, "10:00", 1, 1, "Командная разработка мини-проектов, 40 человек", 3),
    ("elmurat2027", "Встреча клуба Python", 20, "18:30", 2, 2, "Разбор задач, обмен опытом", 2),
    ("elmurat2027", "Защита курсовых проектов", 30, "09:00", 1, 1, "", 1),
    ("anna_ivanova", "Кинопоказ документального фильма", 15, "19:00", 3, 2, "Показ и обсуждение, до 60 мест", 3),
    ("anna_ivanova", "Мастер-класс по дизайну интерфейсов", 25, "14:00", 2, 1, "Работа в Figma", 2),
    ("petrov_pavel", "Лекция по кибербезопасности", 18, "16:00", 1, 2, "Открытая лекция для студентов", 1),
    ("petrov_pavel", "Турнир по настольным играм", 40, "12:00", 2, 1, "", 1),
]


def main():
    db = get_db()
    for login, password, fio, email, phone in USERS:
        if not User.find_by_login(login):
            User({"login": login, "password": password, "fio": fio, "email": email, "phone": phone}).save()
    admin = User.find_by_login("Conf2027")
    for login, name, offset, time_, room, pay, desc, final_status in REQUESTS:
        user = User.find_by_login(login)
        req = Request({
            "user_id": user["id"], "event_name": name,
            "date": (date.today() + timedelta(days=offset)).isoformat(), "start_time": time_,
            "room_id": room, "payment_method_id": pay, "description": desc,
        })
        request_id = req.save()
        for status in range(2, final_status + 1):
            Request.set_status(request_id, status, admin["id"])
    # два отзыва на завершённые заявки
    for title, text, rating in (
        ("Хакатон студентов колледжа", "Помещение удобное, проектор и розетки работали нормально. Спасибо!", 5),
        ("Кинопоказ документального фильма", "Звук хороший, но в зале было немного прохладно.", 4),
    ):
        row = db.one("SELECT r.id, u.login FROM request r JOIN event e ON e.id=r.event_id JOIN user u ON u.id=r.user_id WHERE e.name = ?", (title,))
        Review({"request_id": row["id"], "login": row["login"], "text": text, "rating": rating}).save()
    print("демо-данные добавлены")


if __name__ == "__main__":
    main()
