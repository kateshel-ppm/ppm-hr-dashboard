# -*- coding: utf-8 -*-
"""Пересобирает вкладку «Кол-во сотрудников».

Цифры по рассадке берём из самих вкладок рассадки (а не пересчитываем
заново) — тогда аналитика гарантированно сходится с тем, что в них видно.
Общие цифры по компании — из «Штат 21 09 26».
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Кол-во сотрудников"
MAIN = "Рассадка по отделам 21.09.26"
VARIANT = "Рассадка — все в новом офисе"
NCOLS = 6

CAPACITY = {"Новый офис": 41, "Остоженка · левое крыло": 27,
            "Остоженка · правое крыло": 20}
EXCLUDED_DEPS = {"MAZE", "ВЭД"}

NAVY = {"red": 0.114, "green": 0.180, "blue": 0.333}
BLUE = {"red": 0.180, "green": 0.459, "blue": 0.714}
PALE = {"red": 0.867, "green": 0.922, "blue": 0.969}
AMBER = {"red": 1.0, "green": 0.949, "blue": 0.800}
RED = {"red": 0.976, "green": 0.882, "blue": 0.882}
WHITE = {"red": 1, "green": 1, "blue": 1}
INK = {"red": 0.114, "green": 0.180, "blue": 0.333}
MUTED = {"red": 0.60, "green": 0.62, "blue": 0.66}
LINE = {"red": 0.851, "green": 0.867, "blue": 0.886}

token = access_token(load_credentials())


def read(tab):
    return call(token, "GET", f"{SID}/values/{quote(tab)}").get("values", [])


def seat_body(tab):
    v = read(tab)
    return [r + [""] * (9 - len(r)) for r in v[4:]
            if len(r) > 8 and str(r[8]).strip() in ("работает", "вакансия", "резерв")]


main = seat_body(MAIN)
variant = seat_body(VARIANT)

# ── по отделам (двухофисный вариант) ──
dep_work, dep_vac, dep_res, dep_zone = Counter(), Counter(), Counter(), defaultdict(Counter)
for r in main:
    dep, st = r[3].strip(), r[8].strip()
    if st == "работает":
        dep_work[dep] += 1
    elif st == "вакансия":
        dep_vac[dep] += 1
    else:
        dep_res[dep] += 1
    if st != "резерв":
        dep_zone[dep][r[1].strip()] += 1

# ── по зонам ──
zone_taken, zone_res = Counter(), Counter()
for r in main:
    z = r[1].strip()
    (zone_res if r[8].strip() == "резерв" else zone_taken)[z] += 1

# ── штат целиком ──
rows = [l.rstrip("\n").split("\t") for l in open("shtat.tsv", encoding="utf-8")]
data = [r + [""] * (12 - len(r)) for r in rows[1:] if any(c.strip() for c in r)]
FIO, POS, DEP, VAC, FMT, CITY = 3, 6, 7, 8, 9, 10


def is_vac(r):
    return r[FIO].strip() == "Вакансия" or r[VAC].strip() == "Вакансия"


def dep_of(r):
    return r[DEP].strip()


def in_seating(r):
    return (r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")
            and dep_of(r) not in EXCLUDED_DEPS)


all_dep, msk_dep, out_dep, vac_dep = Counter(), Counter(), Counter(), Counter()
for r in data:
    d = dep_of(r)
    all_dep[d] += 1
    if is_vac(r):
        vac_dep[d] += 1
    if in_seating(r):
        msk_dep[d] += 1
    else:
        out_dep[d] += 1

fmt_cnt = Counter((r[FMT].strip() or "не указан") for r in data if not is_vac(r))
city_cnt = Counter(r[CITY].strip() for r in data if not is_vac(r))

# ── строки ──
values, kind = [], []


def put(row, k):
    values.append([str(c) for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


total_seats = len(main)
var_seats = len(variant)
put(["АНАЛИТИКА ПО ШТАТУ И РАССАДКЕ"], "title")
put([f"Источник: «Штат 21 09 26» и вкладки рассадки · всего строк в штате "
     f"{len(data)} · пересобрано автоматически"], "sub")
put([], "blank")

# 1. отделы
put(["1. Рассадка по отделам — вариант с двумя площадками"], "sect")
put(["Отдел", "Работают", "Вакансии", "Резерв", "Нужно мест", "Где сидят"], "head")
deps = sorted(set(dep_work) | set(dep_vac) | set(dep_res),
              key=lambda d: -(dep_work[d] + dep_vac[d] + dep_res[d]))
for d in deps:
    need = dep_work[d] + dep_vac[d] + dep_res[d]
    zones = ", ".join(z.replace("Остоженка · ", "Ост. ") for z, _ in dep_zone[d].most_common())
    put([d, dep_work[d], dep_vac[d], dep_res[d], need, zones], "row")
put(["ИТОГО", sum(dep_work.values()), sum(dep_vac.values()),
     sum(dep_res.values()), total_seats, f"{len(deps)} отделов"], "total")
put([], "blank")

# 2. зоны
put(["2. Загрузка площадок"], "sect")
put(["Зона", "Занято", "Резерв", "Нужно", "Ёмкость", "Свободно / дефицит"], "head")
tc = tt = tr = 0
for z, cap in CAPACITY.items():
    taken, res = zone_taken[z], zone_res[z]
    need = taken + res
    tc += cap; tt += taken; tr += res
    diff = cap - need
    put([z, taken, res, need, cap,
         f"свободно {diff}" if diff >= 0 else f"НЕ ХВАТАЕТ {-diff}"],
        "row" if diff >= 0 else "bad")
put(["ИТОГО", tt, tr, tt + tr, tc,
     f"свободно {tc - tt - tr}" if tc >= tt + tr else f"НЕ ХВАТАЕТ {tt + tr - tc}"], "total")
put(["Вариант «все в новом офисе»", "", "", var_seats, "—",
     "одна площадка, ограничений нет"], "note")
put([], "blank")

# 3. штат целиком
put(["3. Штат целиком: кто попадает в московскую рассадку"], "sect")
put(["Отдел", "Всего в штате", "В рассадке", "Вне рассадки", "из них вакансий", ""], "head")
for d in sorted(all_dep, key=lambda d: -all_dep[d]):
    put([d, all_dep[d], msk_dep[d], out_dep[d], vac_dep[d], ""], "row")
put(["ИТОГО", sum(all_dep.values()), sum(msk_dep.values()),
     sum(out_dep.values()), sum(vac_dep.values()), ""], "total")
put(["Вне рассадки — удалённые и сотрудники других городов, "
     "а также отделы MAZE и ВЭД (исключены по решению)", "", "", "", "", ""], "note")
put([], "blank")

# 4. формат и города
put(["4. Формат работы и география (только занятые позиции)"], "sect")
put(["Формат работы", "Человек", "Доля", "Город", "Человек", ""], "head")
people_total = sum(fmt_cnt.values())
fmts = fmt_cnt.most_common()
cities = city_cnt.most_common(10)
for i in range(max(len(fmts), len(cities))):
    a = fmts[i] if i < len(fmts) else ("", "")
    b = cities[i] if i < len(cities) else ("", "")
    share = f"{a[1] * 100 // people_total}%" if a[0] else ""
    put([a[0], a[1], share, b[0], b[1], ""], "row")
put(["ИТОГО", people_total, "100%", f"{len(city_cnt)} городов",
     sum(city_cnt.values()), ""], "total")

# ── запись и оформление ──
_meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,sheetId,gridProperties))")
_props = next(x["properties"] for x in _meta["sheets"] if x["properties"]["title"] == TAB)
sheet_id = _props["sheetId"]
MAXROWS = _props["gridProperties"]["rowCount"]
MAXCOLS = _props["gridProperties"]["columnCount"]
print(f"лист {TAB}: {MAXROWS} строк x {MAXCOLS} колонок")
call(token, "POST", f"{SID}:batchUpdate",
     {"requests": [{"unmergeCells": {"range": {"sheetId": sheet_id}}}]})
call(token, "POST", f"{SID}/values/{quote(TAB)}:clear", {})
res = call(token, "PUT", f"{SID}/values/{quote(TAB)}?valueInputOption=RAW",
           {"values": values})
print("записано ячеек:", res.get("updatedCells"))

N = len(values)


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

req = [
    {"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"hideGridlines": True}},
        "fields": "gridProperties.hideGridlines"}},
    # сброс на всю ширину листа, а не только на наши 6 колонок, —
    # иначе справа остаётся оформление от прежней версии вкладки
    fmt(rng(0, min(N + 40, MAXROWS), 0, MAXCOLS), FULL, backgroundColor=WHITE,
        textFormat=font(), verticalAlignment="MIDDLE", wrapStrategy="CLIP",
        padding=PAD),
    {"updateBorders": {
        "range": rng(0, min(N + 40, MAXROWS), NCOLS, MAXCOLS),
        "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
        "left": {"style": "NONE"}, "right": {"style": "NONE"},
        "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"}}},
]
# рамки ниже данных снимаем, только если под данными реально есть строки
if N < MAXROWS:
    req.append({"updateBorders": {
        "range": rng(N, min(N + 40, MAXROWS)),
        "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
        "left": {"style": "NONE"}, "right": {"style": "NONE"},
        "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"}}})
for i, w in enumerate([270, 110, 110, 120, 110, 260]):
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
    elif k in ("sub", "note"):
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}}
                if k == "sub" else
                fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                    textFormat=font(9, italic=True, color=MUTED),
                    verticalAlignment="MIDDLE", padding=PAD)]
        if k == "sub":
            req.append(fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                           textFormat=font(10, color=MUTED),
                           verticalAlignment="MIDDLE", padding=PAD))
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
    elif k == "total":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=PALE,
                       textFormat=font(10, bold=True, color=INK),
                       verticalAlignment="MIDDLE", padding=PAD))
    elif k == "bad":
        req.append(fmt(rng(i, i + 1), "userEnteredFormat.backgroundColor",
                       backgroundColor=RED))

# числа по центру во всех таблицах
for i, k in enumerate(kind):
    if k in ("row", "total", "bad"):
        req.append(fmt(rng(i, i + 1, 1, 5), "userEnteredFormat.horizontalAlignment",
                       horizontalAlignment="CENTER"))
# рамки только вокруг таблиц
start = None
for i, k in enumerate(kind + ["blank"]):
    if k in ("head", "row", "total", "bad"):
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
problems = [f"строка {i+1}" for i, w in enumerate(values)
            if [c.strip() for c in w] !=
            [c.strip() for c in (back[i] if i < len(back) else []) + [""] * NCOLS][:NCOLS]]
assert not problems, f"расхождения после записи: {problems[:10]}"
print(f"сверка пройдена: {N} строк совпадают")
print(f"\nрассадка: {total_seats} мест | вариант одной площадки: {var_seats}")
print(f"штат: {len(data)} строк, в рассадке {sum(msk_dep.values())}, вне {sum(out_dep.values())}")
