"""Замер производительности страниц: с анимациями и без них (prefers-reduced-motion).

Запуск (сайт должен работать): python tools/measure_perf.py [адрес]
Показывает средние значения за 5 загрузок каждой страницы.
"""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
RUNS = 5
PAGES = ["/", "/dashboard", "/profile", "/admin"]

# собираем сдвиги вёрстки (CLS), долгие задачи и время первой отрисовки
HOOK = """
window.__m = {cls: 0, long: 0, lcp: 0};
new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) window.__m.cls += e.value; })).observe({type: 'layout-shift', buffered: true});
new PerformanceObserver(l => l.getEntries().forEach(() => window.__m.long++)).observe({type: 'longtask', buffered: true});
new PerformanceObserver(l => l.getEntries().forEach(e => window.__m.lcp = e.startTime)).observe({type: 'largest-contentful-paint', buffered: true});
"""


def metric(d, name):
    return {m["name"]: m["value"] for m in d.execute_cdp_cmd("Performance.getMetrics", {})["metrics"]}[name]


def login(d, user, password):
    d.get(BASE + "/login")
    d.find_element(By.ID, "login").send_keys(user)
    d.find_element(By.ID, "password").send_keys(password)
    d.find_element(By.CSS_SELECTOR, "#login-form button[type=submit]").click()
    time.sleep(1.2)


def measure(d, page, reduce_motion):
    d.execute_cdp_cmd("Emulation.setEmulatedMedia", {"features": [
        {"name": "prefers-reduced-motion", "value": "reduce" if reduce_motion else "no-preference"}]})
    rows = []
    for _ in range(RUNS):
        d.get("about:blank")
        d.execute_cdp_cmd("Performance.enable", {})
        d.get(BASE + page)
        time.sleep(1.5)
        m = d.execute_script("return window.__m")
        rows.append((metric(d, "TaskDuration") * 1000, metric(d, "ScriptDuration") * 1000,
                     metric(d, "LayoutCount"), metric(d, "RecalcStyleCount"), m["cls"], m["long"], m["lcp"]))
    return [sum(r[i] for r in rows) / RUNS for i in range(7)]


o = Options()
o.add_argument("--headless=new")
d = webdriver.Chrome(options=o)
d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": HOOK})
login(d, "Conf2027", "Demo77")
head = f"{'страница':11}{'режим':16}{'задачи,мс':>10}{'скрипты,мс':>11}{'layout':>7}{'style':>7}{'CLS':>7}{'долгих':>7}{'LCP,мс':>8}"
print(head)
for page in PAGES:
    for reduce_motion in (False, True):
        r = measure(d, page, reduce_motion)
        mode = "без анимаций" if reduce_motion else "с анимациями"
        print(f"{page:11}{mode:16}{r[0]:>10.0f}{r[1]:>11.0f}{r[2]:>7.0f}{r[3]:>7.0f}{r[4]:>7.3f}{r[5]:>7.0f}{r[6]:>8.0f}")
d.quit()
