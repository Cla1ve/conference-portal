import re
from datetime import date, datetime

LOGIN_RE = re.compile(r"^[A-Za-z0-9_]{6,30}$")
PHONE_RE = re.compile(r"^8\(\d{3}\)-\d{3}-\d{2}-\d{2}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
FIO_RE = re.compile(r"^[А-Яа-яЁё\-]+( [А-Яа-яЁё\-]+){1,2}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def check_login(login):
    if not LOGIN_RE.match(login or ""):
        return "Логин: от 6 до 30 символов, только латиница, цифры и _"
    return None


def check_password(password):
    password = password or ""
    if len(password) < 8:
        return "Пароль должен быть не короче 8 символов"
    if not password.strip():
        return "Пароль не может состоять из одних пробелов"
    return None


def check_fio(fio):
    if not FIO_RE.match((fio or "").strip()):
        return "ФИО: 2-3 слова кириллицей, например Иванов Иван Иванович"
    return None


def check_phone(phone):
    if not PHONE_RE.match(phone or ""):
        return "Телефон в формате 8(900)-123-45-67"
    return None


def check_email(email):
    if not EMAIL_RE.match(email or ""):
        return "Введите корректный email"
    return None


def check_event_name(name):
    name = (name or "").strip()
    if len(name) < 3 or len(name) > 200:
        return "Название мероприятия: от 3 до 200 символов"
    return None


def check_date(value):
    try:
        d = datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        return "Укажите дату"
    if d < date.today():
        return "Дата не может быть в прошлом"
    return None


def check_time(value):
    if not TIME_RE.match(value or ""):
        return "Время в формате ЧЧ:ММ"
    return None


def check_not_past(date_value, time_value):
    """Заявка на сегодня принимается только на время, которое ещё не наступило."""
    try:
        moment = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None   # неверный формат уже поймали отдельными проверками
    if moment < datetime.now():
        return "Это время уже прошло, выберите более позднее"
    return None


def check_rating(value):
    try:
        ok = 1 <= int(value) <= 5
    except (TypeError, ValueError):
        ok = False
    return None if ok else "Оценка от 1 до 5"


def check_review_text(text):
    text = (text or "").strip()
    if not text:
        return "Напишите текст отзыва"
    if len(text) > 2000:
        return "Отзыв слишком длинный (максимум 2000 символов)"
    return None


def collect(errors):
    """Оставляет в словаре только поля с ошибками."""
    return {k: v for k, v in errors.items() if v}
