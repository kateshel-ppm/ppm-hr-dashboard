# -*- coding: utf-8 -*-
"""Обновляет вкладку «Аналитика» — баланс мест против потребности.

Ёмкости площадок берём из прежней версии вкладки (это исходные данные
по помещениям, их считает не скрипт). Потребность — из «Штат 21 09 26»
и вкладок рассадки.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, load_credentials, quote  # noqa: E402

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Аналитика"
MAIN = "Рассадка по отделам 21.09.26"
VARIANT = "Рассадка — все в новом офисе"
NCOLS = 5

# ёмкости помещений — исходные данные, не пересчитываются.
# 4 этаж Остоженки в переезде не участвует и из расчёта исключён.
CAP_RIGHT, CAP_LEFT = 20, 27
CAP_FLOOR2 = CAP_RIGHT + CAP_LEFT          # 47
CAP_OSTOZHENKA = CAP_FLOOR2                # 47
CAP_NEW_BASE, CAP_NEW_RESERVE = 33, 8
CAP_NEW = CAP_NEW_BASE + CAP_NEW_RESERVE   # 41
CAP_ALL = CAP_OSTOZHENKA + CAP_NEW         # 88

ZONE_CAP = {"Новый офис": CAP_NEW,
            "Остоженка · левое крыло": CAP_LEFT,
            "Остоженка · правое крыло": CAP_RIGHT}

NAVY = {"red": 0.114, "green": 0.180, "blue": 0.333}
BLUE = {"red": 0.180, "green": 0.459, "blue": 0.714}
PALE = {"red": 0.867, "green": 0.922, "blue": 0.969}
RED = {"red": 0.976, "green": 0.882, "blue": 0.882}
GREEN = {"red": 0.886, "green": 0.945, "blue": 0.898}
WHITE = {"red": 1, "green": 1, "blue": 1}
INK = {"red": 0.114, "green": 0.180, "blue": 0.333}
MUTED = {"red": 0.60, "green": 0.62, "blue": 0.66}
LINE = {"red": 0.851, "green": 0.867, "blue": 0.886}

token = access_token(load_credentials())


def read(tab):
    return call(token, "GET", f"{SID}/values/{quote(tab)}").get("values", [])


def seat_body(tab):
    return [r + [""] * (9 - len(r)) for r in read(tab)[4:]
            if len(r) > 8 and str(r[8]).strip() in ("работает", "вакансия", "резерв")]


main, variant = seat_body(MAIN), seat_body(VARIANT)
st = Counter(r[8].strip() for r in main)
people, vacs, reserve = st["работает"], st["вакансия"], st["резерв"]
need = people + vacs + reserve

occ, res = Counter(), Counter()
for r in main:
    (res if r[8].strip() == "резерв" else occ)[r[1].strip()] += 1

rows_src = [l.rstrip("\n").split("\t") for l in open("shtat.tsv", encoding="utf-8")]
data = [r + [""] * (12 - len(r)) for r in rows_src[1:] if any(c.strip() for c in r)]

values, kind = [], []


def put(row, k):
    values.append([str(c) for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


put(["АНАЛИТИКА: МЕСТА ПРОТИВ ПОТРЕБНОСТИ"], "title")
put([f"Потребность — по вкладке «Штат 21 09 26» и рассадке · "
     f"ёмкости помещений взяты из прежней версии вкладки"], "sub")
put([], "blank")

put(["1. Сколько мест есть"], "sect")
put(["Площадка", "Мест", "", "", ""], "head")
put(["Остоженка, 2 этаж — всего", CAP_FLOOR2], "row")
put(["    правое крыло", CAP_RIGHT], "sub_row")
put(["    левое крыло", CAP_LEFT], "sub_row")
put(["Итого Остоженка", CAP_OSTOZHENKA], "total")
put(["Новый офис — без резерва", CAP_NEW_BASE], "row")
put(["    резерв под 1-3 вакансии", CAP_NEW_RESERVE], "sub_row")
put(["Итого новый офис", CAP_NEW], "total")
put(["ВСЕГО МЕСТ", CAP_ALL], "grand")
put([], "blank")

put(["2. Сколько мест нужно"], "sect")
put(["Потребность", "Мест", "", "", ""], "head")
put(["Сотрудники — Москва, офис и гибрид", people], "row")
put(["Открытые вакансии", vacs], "row")
put(["Резерв — по одному месту на отдел", reserve], "row")
put(["ИТОГО НУЖНО МЕСТ", need], "grand")
put(["Без отделов MAZE и ВЭД; удалённые и другие города мест не занимают",
     "", "", "", ""], "note")
put([], "blank")

put(["3. Баланс"], "sect")
put(["Сценарий", "Мест", "Нужно", "Разница", "Вывод"], "head")
used_now = CAP_FLOOR2 + CAP_NEW
d = used_now - need
put(["Два адреса: Остоженка 2 этаж + новый офис", used_now, need, d,
     f"запас {d}" if d > 1 else ("хватает впритык" if d >= 0 else f"не хватает {-d}")],
    "good" if d > 1 else ("row" if d >= 0 else "bad"))
put(["Всё в новом офисе (одна площадка)", CAP_NEW, len(variant),
     CAP_NEW - len(variant),
     f"нужно помещение на {len(variant)} мест"], "bad")
put([], "blank")

put(["4. По зонам текущей рассадки"], "sect")
put(["Зона", "Занято", "Резерв", "Ёмкость", "Дефицит / запас"], "head")
for z, cap in ZONE_CAP.items():
    n = occ[z] + res[z]
    d = cap - n
    put([z, occ[z], res[z], cap,
         f"запас {d}" if d >= 0 else f"не хватает {-d}"],
        "row" if d >= 0 else "bad")
tot_cap = sum(ZONE_CAP.values())
put(["ИТОГО", sum(occ.values()), sum(res.values()), tot_cap,
     f"запас {tot_cap - need}" if tot_cap >= need else f"не хватает {need - tot_cap}"],
    "grand")
put(["В переезде участвуют только 2 этаж Остоженки и новый офис", "", "", "", ""],
    "note")

# ── запись ──
meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,sheetId,gridProperties))")
props = next(x["properties"] for x in meta["sheets"] if x["properties"]["title"] == TAB)
sheet_id = props["sheetId"]
MAXROWS = props["gridProperties"]["rowCount"]
MAXCOLS = props["gridProperties"]["columnCount"]
print(f"лист {TAB}: {MAXROWS} x {MAXCOLS}")

# Снимаем слияния и закрепление: через границу закреплённых колонок
# объединять ячейки нельзя, а заголовки секций у нас на всю ширину.
call(token, "POST", f"{SID}:batchUpdate", {"requests": [
    {"unmergeCells": {"range": {"sheetId": sheet_id}}},
    {"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"frozenRowCount": 0,
                                          "frozenColumnCount": 0}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
]})
call(token, "POST", f"{SID}/values/{quote(TAB)}:clear", {})
r = call(token, "PUT", f"{SID}/values/{quote(TAB)}?valueInputOption=RAW",
         {"values": values})
print("записано ячеек:", r.get("updatedCells"))

N = len(values)

# размер листа перечитываем ПОСЛЕ записи: запись могла его расширить
meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,gridProperties))")
props = next(x["properties"] for x in meta["sheets"] if x["properties"]["title"] == TAB)
MAXROWS = props["gridProperties"]["rowCount"]
MAXCOLS = props["gridProperties"]["columnCount"]
print(f"лист после записи: {MAXROWS} x {MAXCOLS}")


def rng(r0, r1, c0=0, c1=NCOLS):
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


FULL = ("userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,"
        "verticalAlignment,wrapStrategy,padding)")
PAD = {"top": 2, "bottom": 2, "left": 8, "right": 8}
TAIL = min(N + 40, MAXROWS)

req = [
    {"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"hideGridlines": True}},
        "fields": "gridProperties.hideGridlines"}},
    fmt(rng(0, TAIL, 0, MAXCOLS), FULL, backgroundColor=WHITE, textFormat=font(),
        verticalAlignment="MIDDLE", wrapStrategy="CLIP", padding=PAD),
]
# границы справа от нашей таблицы: заливку сбрасывает FULL, рамки — нет
if MAXCOLS > NCOLS:
    req.append({"updateBorders": {
        "range": rng(0, TAIL, NCOLS, MAXCOLS),
        "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
        "left": {"style": "NONE"}, "right": {"style": "NONE"},
        "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"}}})
if N < TAIL:
    req.append({"updateBorders": {
        "range": rng(N, TAIL, 0, MAXCOLS),
        "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
        "left": {"style": "NONE"}, "right": {"style": "NONE"},
        "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"}}})
for i, w in enumerate([340, 100, 100, 110, 270]):
    req.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                  "startIndex": i, "endIndex": i + 1},
        "properties": {"pixelSize": w}, "fields": "pixelSize"}})

for i, k in enumerate(kind):
    if k == "title":
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                    textFormat=font(18, bold=True, color=INK),
                    verticalAlignment="MIDDLE", padding=PAD)]
    elif k == "sub":
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                    textFormat=font(10, color=MUTED),
                    verticalAlignment="MIDDLE", padding=PAD)]
    elif k == "note":
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                    textFormat=font(9, italic=True, color=MUTED),
                    verticalAlignment="MIDDLE", padding=PAD)]
    elif k == "sect":
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                fmt(rng(i, i + 1), FULL, backgroundColor=BLUE,
                    textFormat=font(11, bold=True, color=WHITE),
                    verticalAlignment="MIDDLE",
                    padding={"top": 2, "bottom": 2, "left": 10, "right": 8}),
                {"updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "ROWS",
                              "startIndex": i, "endIndex": i + 1},
                    "properties": {"pixelSize": 28}, "fields": "pixelSize"}}]
    elif k == "head":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=NAVY,
                       textFormat=font(10, bold=True, color=WHITE),
                       horizontalAlignment="CENTER", verticalAlignment="MIDDLE",
                       wrapStrategy="WRAP", padding=PAD))
    elif k == "sub_row":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                       textFormat=font(10, color=MUTED),
                       verticalAlignment="MIDDLE", padding=PAD))
    elif k == "total":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=PALE,
                       textFormat=font(10, bold=True, color=INK),
                       verticalAlignment="MIDDLE", padding=PAD))
    elif k == "grand":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=NAVY,
                       textFormat=font(11, bold=True, color=WHITE),
                       verticalAlignment="MIDDLE", padding=PAD))
    elif k == "bad":
        req.append(fmt(rng(i, i + 1), "userEnteredFormat.backgroundColor",
                       backgroundColor=RED))
    elif k == "good":
        req.append(fmt(rng(i, i + 1), "userEnteredFormat.backgroundColor",
                       backgroundColor=GREEN))

for i, k in enumerate(kind):
    if k in ("row", "sub_row", "total", "grand", "bad", "good"):
        req.append(fmt(rng(i, i + 1, 1, 4), "userEnteredFormat.horizontalAlignment",
                       horizontalAlignment="CENTER"))

start = None
for i, k in enumerate(kind + ["blank"]):
    if k in ("head", "row", "sub_row", "total", "grand", "bad", "good"):
        start = i if start is None else start
    elif start is not None:
        req.append({"updateBorders": {
            "range": rng(start, i),
            "innerHorizontal": {"style": "SOLID", "color": LINE},
            "innerVertical": {"style": "SOLID", "color": LINE}}})
        start = None

call(token, "POST", f"{SID}:batchUpdate", {"requests": req})
print(f"оформление: {len(req)} операций, {N} строк")

back = read(TAB)
bad = [i + 1 for i, w in enumerate(values)
       if [c.strip() for c in w]
       != [c.strip() for c in ((back[i] if i < len(back) else []) + [""] * NCOLS)][:NCOLS]]
assert not bad, f"расхождения после записи в строках: {bad[:10]}"
print(f"сверка пройдена: {N} строк совпадают")
print(f"\nнужно {need} мест (люди {people} + вакансии {vacs} + резерв {reserve})")
print(f"мест в игре: {CAP_ALL} (Остоженка 2 этаж {CAP_FLOOR2} + новый офис {CAP_NEW})")
