# -*- coding: utf-8 -*-
"""Доводка оформления вкладки: ширины колонок и визуальная иерархия."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SPREADSHEET = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Рассадка по отделам 21.09.26"
NCOLS = 9

MUTED = {"red": 0.60, "green": 0.62, "blue": 0.66}
INK = {"red": 0.114, "green": 0.180, "blue": 0.333}
AMBER_INK = {"red": 0.478, "green": 0.325, "blue": 0.020}

token = access_token(load_credentials())
sheet_id = get_tabs(token, SPREADSHEET)[TAB]

grid = call(token, "GET", f"{SPREADSHEET}/values/{quote(TAB)}")
rows = grid.get("values", [])
N = len(rows)


def rng(r0, r1, c0, c1):
    return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
            "startColumnIndex": c0, "endColumnIndex": c1}


def fmt(range_, fields, **f):
    return {"repeatCell": {"range": range_, "cell": {"userEnteredFormat": f},
                           "fields": fields}}


def font(size=10, bold=False, italic=False, color=None):
    t = {"fontFamily": "Inter", "fontSize": size, "bold": bold, "italic": italic}
    if color:
        t["foregroundColor"] = color
    return t


req = []

# 1. ширины: сузить повторяющиеся колонки, расширить содержательные
for i, w in enumerate([50, 180, 244, 100, 200, 350, 178, 80, 92]):
    req.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                  "startIndex": i, "endIndex": i + 1},
        "properties": {"pixelSize": w}, "fields": "pixelSize"}})

# 2. классифицируем строки по содержимому первой ячейки
kinds = []
for r in rows:
    first = (r[0] if r else "").strip()
    status = (r[8].strip() if len(r) > 8 else "")
    if status == "вакансия":
        kinds.append("vac")
    elif status == "резерв":
        kinds.append("res")
    elif status == "работает":
        kinds.append("row")
    else:
        kinds.append("other")

# 3. приглушаем повторяющиеся «Офис / зона» и «Блок», выделяем статус
runs = []
for i, k in enumerate(kinds):
    if k in ("row", "vac"):
        if runs and runs[-1][1] == i and runs[-1][2] == k:
            runs[-1] = (runs[-1][0], i + 1, k)
        else:
            runs.append((i, i + 1, k))

for a, b, k in runs:
    # колонки «Офис / зона» и «Блок» — служебные, уводим на второй план
    req.append(fmt(rng(a, b, 1, 3), "userEnteredFormat.textFormat",
                   textFormat=font(9, color=MUTED)))
    # ФИО — смысловой якорь строки
    req.append(fmt(rng(a, b, 4, 5), "userEnteredFormat.textFormat",
                   textFormat=font(10, bold=(k == "row"), color=INK)))
    # статус
    if k == "vac":
        req.append(fmt(rng(a, b, 8, 9), "userEnteredFormat.textFormat",
                       textFormat=font(9, bold=True, color=AMBER_INK)))
    else:
        req.append(fmt(rng(a, b, 8, 9), "userEnteredFormat.textFormat",
                       textFormat=font(9, color=MUTED)))
    # «Формат работы» тоже второстепенен
    req.append(fmt(rng(a, b, 7, 8), "userEnteredFormat.textFormat",
                   textFormat=font(9, color=MUTED)))

# 4. перенос длинных должностей вместо обрезки
req.append(fmt(rng(4, N, 5, 6), "userEnteredFormat.wrapStrategy",
               wrapStrategy="WRAP"))
req.append(fmt(rng(4, N, 6, 7), "userEnteredFormat.wrapStrategy",
               wrapStrategy="WRAP"))

call(token, "POST", f"{SPREADSHEET}:batchUpdate", {"requests": req})
print(f"доводка применена: {len(req)} операций, строк {N}, блоков {len(runs)}")
