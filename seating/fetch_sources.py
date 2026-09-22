# -*- coding: utf-8 -*-
"""Скачивает оба источника и собирает объединённый shtat.tsv.

  Штат 21 09 26  (файл переезда)      → shtat_now.tsv, shtat_pereezd.tsv
  ШТАТКА         (Список сотрудников) → shtatka.tsv   (только нужные колонки)
  merge_source.py                     → shtat.tsv     (то, что читают сборщики)

Из ШТАТКИ берём только A–D, F–G, P: ФИО, Статус, Должность, Отдел,
Формат работы, Город, Прямой руководитель. Зарплаты, телефоны и даты
рождения в тот же файл не попадают.
"""
import csv
import os
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, load_credentials, quote  # noqa: E402

PEREEZD = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
SOTRUDNIKI = "1EqDdNUftgFCcVlqZ-lw_6VdHOYLh2jbMwryP1-K9BWk"

token = access_token(load_credentials())

# 1. вкладка переезда целиком
rows = call(token, "GET", f"{PEREEZD}/values/{quote('Штат 21 09 26')}")["values"]
for name in ("shtat_now.tsv", "shtat_pereezd.tsv"):
    with open(name, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter="\t").writerows(rows)
print(f"Штат 21 09 26: {len(rows) - 1} строк → shtat_now.tsv, shtat_pereezd.tsv")

# 2. ШТАТКА — только нужные колонки
ranges = "&".join("ranges=" + urllib.parse.quote(f"'ШТАТКА'!{r}")
                  for r in ("A:D", "F:G", "P:P"))
res = call(token, "GET",
           f"{SOTRUDNIKI}/values:batchGet?{ranges}&majorDimension=COLUMNS")
cols = [c for vr in res["valueRanges"] for c in vr.get("values", [])]
n = max(len(c) for c in cols)
out = [[(c[i].strip() if i < len(c) else "") for c in cols] for i in range(n)]
out = [r for r in out if any(r)]
with open("shtatka.tsv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f, delimiter="\t").writerows(out)
print(f"ШТАТКА: {len(out) - 1} строк → shtatka.tsv  (колонки: {out[0]})")

# 3. объединение
subprocess.run([sys.executable, "merge_source.py"], check=True)
