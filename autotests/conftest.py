"""Общие настройки автотестов: запуск сайта, браузер, скриншот при падении теста."""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS = Path(__file__).resolve().parent / "screenshots"
PORT = int(os.environ.get("TEST_PORT", "5055"))
BASE_URL = f"http://127.0.0.1:{PORT}"

# тесты работают с отдельной временной базой, рабочую не трогаем
_tmp = tempfile.mkdtemp(prefix="conf_autotests_")
DB_FILE = os.path.join(_tmp, "test.db")
os.environ["DATABASE"] = DB_FILE
os.environ["SECRET_KEY"] = "autotest-secret"

sys.path.insert(0, str(ROOT))
import init_db  # noqa: E402
from backend.themes import THEMES  # noqa: E402
from backend.models import User  # noqa: E402

DEMO_USER = {"login": "autotest_user", "password": "Password123", "fio": "Тестов Тест Тестович",
             "phone": "8(900)-100-20-30", "email": "autotest@example.ru"}
ADMIN = {"login": "Conf2027", "password": "Demo77"}

# какая тематика проверяется: THEME=sport python -m pytest autotests ...
THEME_NAME = os.environ.get("THEME", "conference")
THEME = THEMES[THEME_NAME]


def pytest_configure(config):
    config.addinivalue_line("markers", "demo_failure: тест, который падает специально (для показа скриншота при ошибке)")


@pytest.fixture(scope="session")
def live_server():
    """Поднимает сайт на отдельном порту и ждёт, пока он ответит."""
    init_db.run_migrations(DB_FILE, quiet=True)
    init_db.seed_dictionaries(DB_FILE, THEME_NAME)
    User(dict(DEMO_USER)).save()
    env = dict(os.environ, PORT=str(PORT))
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=str(ROOT), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            urllib.request.urlopen(BASE_URL + "/", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError("сайт не запустился")
    yield BASE_URL
    proc.terminate()


@pytest.fixture
def driver(live_server):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=ru")
    options.add_argument("--no-sandbox")
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(0)          # только явные ожидания, неявные не используем
    yield drv
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Если тест упал, сохраняем скриншот страницы и подкладываем его в html-отчёт."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        drv = item.funcargs.get("driver")
        if drv is not None:
            SCREENSHOTS.mkdir(exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = SCREENSHOTS / f"FAIL_{item.name}_{stamp}.png"
            drv.save_screenshot(str(path))
            try:
                from pytest_html import extras
                report.extras = getattr(report, "extras", []) + [extras.png(drv.get_screenshot_as_base64())]
            except ImportError:
                pass
            print(f"\nСкриншот при падении: {path}")
