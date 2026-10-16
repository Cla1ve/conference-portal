from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from autotests.pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"
    LOGIN = (By.ID, "login")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.CSS_SELECTOR, "#login-form button[type=submit]")
    FORM_ERROR = (By.ID, "form-error")
    LOGIN_ERROR = (By.CSS_SELECTOR, '[data-error-for="login"]')
    PASSWORD_ERROR = (By.CSS_SELECTOR, '[data-error-for="password"]')

    def login_as(self, login, password):
        self.type(self.LOGIN, login)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)

    def login_and_wait(self, login, password, target="/dashboard"):
        """Входит и ждёт, пока откроется нужная страница (иначе следующий переход оборвёт запрос входа)."""
        self.login_as(login, password)
        self.wait_url_contains(target)

    def password_input_type(self):
        return self.visible(self.PASSWORD).get_attribute("type")


class RegisterPage(BasePage):
    path = "/register"
    FIELDS = ("login", "password", "fio", "phone", "email")
    SUBMIT = (By.CSS_SELECTOR, "#register-form button[type=submit]")
    TOAST = (By.CSS_SELECTOR, "#toasts .toast")

    def fill(self, data):
        for name in self.FIELDS:
            self.type((By.ID, name), data[name])

    def submit(self):
        self.click(self.SUBMIT)

    def error_for(self, name):
        return self.text_of((By.CSS_SELECTOR, f'[data-error-for="{name}"]'))


class DashboardPage(BasePage):
    path = "/dashboard"
    TITLE = (By.TAG_NAME, "h1")
    CARDS = (By.CSS_SELECTOR, "article.request-card")

    def card_titles(self):
        self.visible(self.TITLE)
        return [c.find_element(By.TAG_NAME, "h3").text for c in self.driver.find_elements(*self.CARDS)]


class RequestPage(BasePage):
    path = "/request/new"
    SUBMIT = (By.CSS_SELECTOR, "#request-form button[type=submit]")

    def fill(self, name, date, time_, room, payment):
        self.type((By.ID, "event_name"), name)
        # поля даты и времени в разных браузерах вводятся по-разному, поэтому ставим значения скриптом
        self.driver.execute_script(
            "document.getElementById('date').value = arguments[0]; document.getElementById('start_time').value = arguments[1];", date, time_)
        Select(self.visible((By.ID, "room_id"))).select_by_visible_text(room)
        Select(self.visible((By.ID, "payment_method_id"))).select_by_visible_text(payment)

    def submit(self):
        self.click(self.SUBMIT)
        self.wait_url_contains("/dashboard")


class AdminPage(BasePage):
    path = "/admin"
    CARDS = (By.CSS_SELECTOR, "#admin-cards article")

    def card_with(self, title):
        def find(driver):
            for card in driver.find_elements(*self.CARDS):
                if title in card.text:
                    return card
            return False
        return self.wait.until(find)

    def press_in_card(self, title, button_text):
        card = self.card_with(title)
        for button in card.find_elements(By.TAG_NAME, "button"):
            if button.text == button_text:
                button.click()
                return
        raise AssertionError(f"кнопка «{button_text}» не найдена в карточке «{title}»")

    def status_of(self, title):
        # каждый раз ищем карточку заново: после смены статуса список обновляется
        return self.wait.until(lambda d: self.card_with(title).find_element(By.CSS_SELECTOR, ".status").text)
