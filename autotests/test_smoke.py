"""Задание 5: смоук-тесты собственного приложения (основные сценарии: открытие, регистрация, заявка, админ)."""
import time

from selenium.webdriver.common.by import By

from autotests.conftest import DEMO_USER, ADMIN
from autotests.pages.pages import LoginPage, RegisterPage, DashboardPage, RequestPage, AdminPage


def unique(prefix):
    return f"{prefix}_{int(time.time() * 1000) % 10_000_000}"


def test_smoke_main_page_opens(driver, live_server):
    driver.get(live_server + "/")
    page = LoginPage(driver, live_server)
    assert "Конференции.РФ" in driver.title
    assert page.text_of((By.TAG_NAME, "h1")) == "Проведите своё мероприятие у нас"
    page.visible((By.LINK_TEXT, "Вход"))
    page.visible((By.LINK_TEXT, "Регистрация"))


def test_smoke_guest_is_redirected_from_dashboard(driver, live_server):
    driver.get(live_server + "/dashboard")
    LoginPage(driver, live_server).wait_url_contains("/login")


def test_smoke_registration_of_new_user(driver, live_server):
    login = unique("smoke")
    page = RegisterPage(driver, live_server).open()
    page.fill({"login": login, "password": "Password123", "fio": "Смоков Смок Смокович",
               "phone": "89001112233", "email": login + "@example.ru"})
    page.submit()
    page.wait_text(RegisterPage.TOAST, "Регистрация прошла успешно")
    page.wait_url_contains("/login")
    # после регистрации под новым логином можно войти
    LoginPage(driver, live_server).login_as(login, "Password123")
    page.wait_url_contains("/dashboard")


def test_smoke_user_creates_request_and_sees_it(driver, live_server):
    title = unique("Автотест встреча")
    LoginPage(driver, live_server).open().login_and_wait(DEMO_USER["login"], DEMO_USER["password"])
    request_page = RequestPage(driver, live_server).open()
    request_page.fill(title, "2030-05-20", "12:00", "Коворкинг", "СБП")
    request_page.submit()
    assert title in DashboardPage(driver, live_server).card_titles()


def test_smoke_admin_assigns_event(driver, live_server):
    title = unique("Автотест для админа")
    LoginPage(driver, live_server).open().login_and_wait(DEMO_USER["login"], DEMO_USER["password"])
    request_page = RequestPage(driver, live_server).open()
    request_page.fill(title, "2030-06-10", "10:00", "Аудитория", "При очном посещении")
    request_page.submit()
    DashboardPage(driver, live_server).logout()

    LoginPage(driver, live_server).open().login_and_wait(ADMIN["login"], ADMIN["password"], "/admin")
    admin = AdminPage(driver, live_server)
    assert admin.status_of(title) == "Новая"
    admin.press_in_card(title, "Назначить мероприятие")
    admin.wait.until(lambda d: admin.status_of(title) == "Мероприятие назначено")
