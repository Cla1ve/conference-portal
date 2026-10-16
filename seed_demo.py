"""Тестовые данные для показа и скриншотов.  Запуск: python seed_demo.py"""
from datetime import date, timedelta

from backend import config
from backend.db import get_db
from backend.models import User, Request, Review

USERS = [
    ("elmurat2027", "Student2027", "Маматисаков Элмурат Сапарбекович", "elmurat@example.ru", "8(915)-204-18-36"),
    ("anna_ivanova", "Password123", "Иванова Анна Сергеевна", "anna.ivanova@example.ru", "8(903)-555-12-90"),
    ("petrov_pavel", "Password123", "Петров Павел Игоревич", "petrov@example.ru", "8(926)-777-45-02"),
]

# (логин, название, дней от сегодня, время, помещение, оплата, описание, до какого статуса довести)
CONFERENCE_REQUESTS = [
    ("elmurat2027", "Хакатон студентов колледжа", 12, "10:00", 1, 1, "Командная разработка мини-проектов, 40 человек", 3),
    ("elmurat2027", "Встреча клуба Python", 20, "18:30", 2, 2, "Разбор задач, обмен опытом", 2),
    ("elmurat2027", "Защита курсовых проектов", 30, "09:00", 1, 1, "", 1),
    ("anna_ivanova", "Кинопоказ документального фильма", 15, "19:00", 3, 2, "Показ и обсуждение, до 60 мест", 3),
    ("anna_ivanova", "Мастер-класс по дизайну интерфейсов", 25, "14:00", 2, 1, "Работа в Figma", 2),
    ("petrov_pavel", "Лекция по кибербезопасности", 18, "16:00", 1, 2, "Открытая лекция для студентов", 1),
    ("petrov_pavel", "Турнир по настольным играм", 40, "12:00", 2, 1, "", 1),
]


SPORT_REQUESTS = [
    ("elmurat2027", "Тренировка студенческой команды по футболу", 12, "18:00", 3, 1, "Отработка стандартных положений, 16 человек", 3),
    ("elmurat2027", "Групповое занятие по плаванию", 20, "08:30", 2, 2, "Дорожки для начинающих", 2),
    ("elmurat2027", "Товарищеский матч по баскетболу", 30, "19:00", 1, 1, "", 1),
    ("anna_ivanova", "Турнир по волейболу среди групп", 15, "15:00", 1, 2, "Шесть команд, судья от колледжа", 3),
    ("anna_ivanova", "Утренняя зарядка для сотрудников", 25, "07:45", 1, 1, "Лёгкая разминка 30 минут", 2),
    ("petrov_pavel", "Секция мини-футбола", 18, "20:00", 3, 2, "Еженедельная игра", 1),
    ("petrov_pavel", "Мастер-класс по технике плавания", 40, "12:00", 2, 1, "", 1),
]

CONFERENCE_REVIEWS = [
    ("Хакатон студентов колледжа", "Помещение удобное, проектор и розетки работали нормально. Спасибо!", 5),
    ("Кинопоказ документального фильма", "Звук хороший, но в зале было немного прохладно.", 4),
]
SPORT_REVIEWS = [
    ("Тренировка студенческой команды по футболу", "Газон в хорошем состоянии, освещение нормальное. Спасибо!", 5),
    ("Турнир по волейболу среди групп", "Площадка чистая, сетка натянута хорошо, не хватило скамеек.", 4),
]


def main():
    sport = config.THEME == "sport"
    REQUESTS = SPORT_REQUESTS if sport else CONFERENCE_REQUESTS
    REVIEWS = SPORT_REVIEWS if sport else CONFERENCE_REVIEWS
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
    for title, text, rating in REVIEWS:
        row = db.one("SELECT r.id, u.login FROM request r JOIN event e ON e.id=r.event_id JOIN user u ON u.id=r.user_id WHERE e.name = ?", (title,))
        Review({"request_id": row["id"], "login": row["login"], "text": text, "rating": rating}).save()
    print("демо-данные добавлены")


if __name__ == "__main__":
    main()
