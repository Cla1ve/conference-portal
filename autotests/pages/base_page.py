from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 8


class BasePage:
    """Общие методы для всех страниц. Ждём элементы явно через WebDriverWait."""

    path = "/"

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        # список заявок на странице перерисовывается скриптом, поэтому устаревшие элементы при ожидании пропускаем
        self.wait = WebDriverWait(driver, TIMEOUT, ignored_exceptions=(StaleElementReferenceException,))

    def open(self):
        self.driver.get(self.base_url + self.path)
        return self

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def clickable(self, locator):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def type(self, locator, text):
        field = self.visible(locator)
        field.clear()
        field.send_keys(text)

    def click(self, locator):
        self.clickable(locator).click()

    def text_of(self, locator):
        return self.visible(locator).text

    def wait_text(self, locator, text):
        """Ждём, пока в элементе появится нужный текст."""
        self.wait.until(EC.text_to_be_present_in_element(locator, text))

    def wait_url_contains(self, part):
        self.wait.until(EC.url_contains(part))

    def logout(self):
        from selenium.webdriver.common.by import By
        self.click((By.ID, "logout-btn"))
        self.wait_url_contains("/login")
