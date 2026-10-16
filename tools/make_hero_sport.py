"""Рисует картинку для главной страницы спортивной темы (плоская иллюстрация, как у основной темы).

Запуск: python tools/make_hero_sport.py
Результат: docs/img_source/hero_sport-original.png и frontend/static/img/hero_sport.jpg / .webp
"""
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
S = 2                                  # рисуем в двойном размере, потом уменьшаем (гладкие края)
W, H = 1600 * S, 1000 * S
DARK, MID = (11, 61, 46), (22, 105, 70)
GREEN, LINE, CREAM, LIGHT = (43, 138, 62), (245, 247, 240), (250, 246, 233), (255, 214, 102)


def px(v):
    return int(v * S)


img = Image.new("RGB", (W, H), DARK)
d = ImageDraw.Draw(img)
# фон: вертикальный градиент
for y in range(H):
    k = y / H
    d.line([(0, y), (W, y)], fill=tuple(int(DARK[i] + (MID[i] - DARK[i]) * k) for i in range(3)))

# прожекторы
for x in (330, 800, 1270):
    d.polygon([(px(x - 40), 0), (px(x + 40), 0), (px(x + 150), px(330)), (px(x - 150), px(330))], fill=(60, 120, 96))

# табло
d.rounded_rectangle([px(330), px(170), px(1270), px(400)], px(26), fill=CREAM)
d.rounded_rectangle([px(380), px(205), px(1220), px(365)], px(14), fill=DARK)
d.rectangle([px(330), px(400), px(1270), px(430)], fill=(236, 150, 50))
d.text((px(560), px(250)), "", fill=CREAM)
# счёт: две цифры из прямоугольников-сегментов
def digit(x0, y0, w, h, t, segs):
    pos = {"a": (x0, y0, x0 + w, y0 + t), "b": (x0 + w - t, y0, x0 + w, y0 + h // 2 + t // 2),
           "c": (x0 + w - t, y0 + h // 2 - t // 2, x0 + w, y0 + h), "d": (x0, y0 + h - t, x0 + w, y0 + h),
           "e": (x0, y0 + h // 2 - t // 2, x0 + t, y0 + h), "f": (x0, y0, x0 + t, y0 + h // 2 + t // 2),
           "g": (x0, y0 + h // 2 - t // 2, x0 + w, y0 + h // 2 + t // 2)}
    for s in segs:
        d.rounded_rectangle([px(v) for v in pos[s]], px(4), fill=LIGHT)
digit(500, 235, 70, 110, 14, "abcdef")       # 0
digit(620, 235, 70, 110, 14, "bc")           # 1
d.rectangle([px(760), px(285), px(800), px(297)], fill=LIGHT)
d.rectangle([px(760), px(318), px(800), px(330)], fill=LIGHT)
digit(850, 235, 70, 110, 14, "abdeg")         # 2
digit(970, 235, 70, 110, 14, "abcdfg")        # 9

# поле сверху: белые линии на зелёном
d.rounded_rectangle([px(150), px(500), px(1450), px(950)], px(24), fill=GREEN)
for i in range(7):                             # полосы газона
    x0 = 150 + i * 186
    if i % 2 == 0:
        d.rectangle([px(x0), px(500), px(min(x0 + 186, 1450)), px(950)], fill=(50, 150, 70))
d.rounded_rectangle([px(150), px(500), px(1450), px(950)], px(24), outline=LINE, width=px(8))
d.line([(px(800), px(500)), (px(800), px(950))], fill=LINE, width=px(8))
d.ellipse([px(700), px(625), px(900), px(825)], outline=LINE, width=px(8))
d.ellipse([px(785), px(710), px(815), px(740)], fill=LINE)
for x0, x1 in ((150, 320), (1280, 1450)):      # штрафные площадки
    d.rectangle([px(x0), px(610), px(x1), px(840)], outline=LINE, width=px(8))
# мяч в углу
bx, by, br = 1180, 700, 58
d.ellipse([px(bx - br), px(by - br), px(bx + br), px(by + br)], fill=CREAM, outline=(30, 40, 35), width=px(5))
d.regular_polygon((px(bx), px(by), px(22)), 5, fill=(30, 40, 35))
for ang in range(5):
    import math
    a = math.radians(90 + ang * 72)
    d.line([(px(bx + 22 * math.cos(a)), px(by - 22 * math.sin(a))), (px(bx + 56 * math.cos(a)), px(by - 56 * math.sin(a)))], fill=(30, 40, 35), width=px(4))
# фишки игроков
for (x, y, c) in ((420, 700, (232, 89, 12)), (560, 820, (232, 89, 12)), (1020, 640, (250, 246, 233)), (1060, 840, (250, 246, 233))):
    d.ellipse([px(x - 22), px(y - 22), px(x + 22), px(y + 22)], fill=c, outline=(20, 50, 40), width=px(4))

img = img.filter(ImageFilter.GaussianBlur(0.6))
img = img.resize((1600, 1000), Image.LANCZOS)
# лёгкое зерно, как на основной картинке
random.seed(3)
noise = Image.effect_noise((1600, 1000), 6).convert("RGB")
img = ImageChops.add(img, noise, scale=1, offset=-128)

src = ROOT / "docs" / "img_source" / "hero_sport-original.png"
img.save(src)
small = img.resize((1120, 700), Image.LANCZOS)
out = ROOT / "frontend" / "static" / "img"
small.save(out / "hero_sport.jpg", quality=74, optimize=True, progressive=True)
small.save(out / "hero_sport.webp", quality=68, method=6)
for f in (src, out / "hero_sport.jpg", out / "hero_sport.webp"):
    print(f.name, f.stat().st_size // 1024, "КБ")
