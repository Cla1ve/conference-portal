"""Проверка адаптивности: открывает все страницы на разных ширинах и ищет горизонтальную прокрутку.

Запуск (сайт должен работать): python tools/check_responsive.py [адрес]
"""
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
WIDTHS = [320, 390, 768, 1280]
GUEST = ["/", "/login", "/register", "/nothing-here"]
USER = ["/dashboard", "/request/new", "/profile"]
ADMIN = ["/admin"]

JS = """
const W = document.documentElement.clientWidth;
let bad = 0;
document.querySelectorAll('body *').forEach(e => {
  const r = e.getBoundingClientRect();
  if (r.width && (r.right > W + 1 || r.left < -1) && getComputedStyle(e).display !== 'none') bad++;
});
const top = document.querySelector('main .page-head, main h1, main .form-card, main .hero');
const head = document.querySelector('.topbar').getBoundingClientRect().bottom;
const gap = top ? Math.round(top.getBoundingClientRect().top - head) : -1;
return [document.documentElement.scrollWidth, W, bad, gap];
"""


def login(d, user, password):
    d.delete_all_cookies()
    d.get(BASE + "/login")
    d.find_element(By.ID, "login").send_keys(user)
    d.find_element(By.ID, "password").send_keys(password)
    d.find_element(By.CSS_SELECTOR, "#login-form button[type=submit]").click()
    time.sleep(1.2)


o = Options()
o.add_argument("--headless=new")
d = webdriver.Chrome(options=o)
problems = 0
print(f"{'страница':14}" + "".join(f"  {w:<20}" for w in WIDTHS))
for pages, creds in ((GUEST, None), (USER, ("elmurat2027", "Student2027")), (ADMIN, ("Conf2027", "Demo77"))):
    if creds:
        login(d, *creds)
    else:
        d.delete_all_cookies()
    for page in pages:
        row = f"{page:14}"
        for w in WIDTHS:
            d.execute_cdp_cmd("Emulation.setDeviceMetricsOverride",
                              {"width": w, "height": 844, "deviceScaleFactor": 1, "mobile": w < 768})
            d.get(BASE + page)
            time.sleep(0.8)
            scroll_w, width, bad, gap = d.execute_script(JS)
            ok = scroll_w <= width and bad == 0 and (gap >= 12 or gap < 0)
            problems += 0 if ok else 1
            row += f"  {('ok' if ok else 'ПРОБЛЕМА'):<9} {'отступ ' + str(gap):<10}"
        print(row)
d.quit()
print("проблем:", problems)
sys.exit(1 if problems else 0)
