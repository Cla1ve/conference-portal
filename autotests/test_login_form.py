"""Задание 4: автотесты формы авторизации (Selenium, явные ожидания, Page Object Model)."""
import pytest
from selenium.webdriver.common.by import By

from autotests.conftest import DEMO_USER, ADMIN
from autotests.pages.pages import LoginPage, DashboardPage


@pytest.fixture
def login_page(driver, live_server):
    return LoginPage(driver, live_server).open()


def test_user_login_opens_dashboard(login_page):
    login_page.login_as(DEMO_USER["login"], DEMO_USER["password"])
    login_page.wait_url_contains("/dashboard")
    assert login_page.text_of((By.TAG_NAME, "h1")) == "Мои заявки"


def test_admin_login_opens_admin_panel(login_page):
    login_page.login_as(ADMIN["login"], ADMIN["password"])
    login_page.wait_url_contains("/admin")
    assert login_page.text_of((By.TAG_NAME, "h1")) == "Все заявки"


def test_wrong_password_shows_message(login_page):
    login_page.login_as(DEMO_USER["login"], "wrong-password")
    login_page.wait_text(LoginPage.FORM_ERROR, "Неверный логин или пароль")
    assert "/login" in login_page.driver.current_url


def test_unknown_login_gets_same_message(login_page):
    """Сообщение не должно выдавать, существует ли такой логин."""
    login_page.login_as("no_such_user_123", "whatever123")
    login_page.wait_text(LoginPage.FORM_ERROR, "Неверный логин или пароль")


def test_empty_form_shows_errors_under_fields(login_page):
    login_page.click(LoginPage.SUBMIT)
    login_page.wait_text(LoginPage.LOGIN_ERROR, "Введите логин")
    login_page.wait_text(LoginPage.PASSWORD_ERROR, "Введите пароль")


def test_password_is_hidden(login_page):
    assert login_page.password_input_type() == "password"


def test_logout_returns_to_login(login_page):
    login_page.login_as(DEMO_USER["login"], DEMO_USER["password"])
    login_page.wait_url_contains("/dashboard")
    DashboardPage(login_page.driver, login_page.base_url).logout()
    assert login_page.driver.current_url.endswith("/login")


@pytest.mark.demo_failure
def test_demo_failure_wrong_expectation(login_page):
    """Падает специально: ожидаем неверный текст ошибки, чтобы показать скриншот при падении."""
    login_page.login_as(DEMO_USER["login"], "wrong-password")
    login_page.wait_text(LoginPage.FORM_ERROR, "Пользователь заблокирован")
