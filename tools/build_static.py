"""Минификация CSS и JS: из frontend/static/css и js делает файлы *.min.* в frontend/static/dist.

Запуск:  python tools/build_static.py
Нужны пакеты rcssmin и rjsmin (pip install rcssmin rjsmin). Исходники не меняются.
Сайт сам берёт минифицированные файлы, если они есть (USE_MIN=0 отключает).
"""
import gzip
import sys
from pathlib import Path

import rcssmin
import rjsmin

STATIC = Path(__file__).resolve().parent.parent / "frontend" / "static"
DIST = STATIC / "dist"
DIST.mkdir(exist_ok=True)

total_src = total_min = 0
print(f"{'файл':14}{'исходный':>10}{'минифиц.':>10}{'меньше':>8}{'gzip':>8}")
for folder, minify in (("css", rcssmin.cssmin), ("js", rjsmin.jsmin)):
    for src in sorted((STATIC / folder).glob("*." + folder)):
        text = src.read_text(encoding="utf-8")
        small = minify(text)
        out = DIST / f"{src.stem}.min.{folder}"
        out.write_text(small, encoding="utf-8")
        a, b = len(text.encode("utf-8")), len(small.encode("utf-8"))
        total_src += a
        total_min += b
        print(f"{src.name:14}{a:>10}{b:>10}{100 - b * 100 // a:>7}%{len(gzip.compress(small.encode('utf-8'))):>8}")
print(f"{'всего':14}{total_src:>10}{total_min:>10}{100 - total_min * 100 // total_src:>7}%")
sys.exit(0)
