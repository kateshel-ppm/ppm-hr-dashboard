# -*- coding: utf-8 -*-
"""Вкладка «Аналитика» строго по двум источникам: «Штат 21 09 26» и плану.

Никаких допущений о ёмкости помещений: места считаются по подписям на
схеме. Слева на плане рабочие места подписаны фамилиями, справа — только
должностями (место есть, человек не назначен).
"""
import os
import re
import sys
from collections import Counter, defaultdict

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, load_credentials, quote  # noqa: E402

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Аналитика"
NCOLS = 5

# Границы по горизонтали на схеме.
# Проверено сопоставлением с колонкой «Офис (крыло)» штата: в восточной части
# плана сидят 27 из 28 человек с пометкой «Левое» (кабинеты Л1–Л4), в западной —
# все 29 человек с пометкой «Правое» (кабинеты П0–П7). То есть схема нарисована
# зеркально относительно названий крыльев.
X_WING = 400           # западнее — правое крыло, восточнее — левое
X_SPLIT = 700          # дальше на восток — отдельный блок без фамилий


def region(x):
    if x >= X_SPLIT:
        return "block"
    return "left" if x >= X_WING else "right"

FIO, POS, DEP, ST, FMT, CITY, MGR = 3, 6, 7, 8, 9, 10, 11

NAVY = {"red": 0.114, "green": 0.180, "blue": 0.333}
BLUE = {"red": 0.180, "green": 0.459, "blue": 0.714}
PALE = {"red": 0.867, "green": 0.922, "blue": 0.969}
RED = {"red": 0.976, "green": 0.882, "blue": 0.882}
AMBER = {"red": 1.0, "green": 0.949, "blue": 0.800}
WHITE = {"red": 1, "green": 1, "blue": 1}
INK = {"red": 0.114, "green": 0.180, "blue": 0.333}
MUTED = {"red": 0.60, "green": 0.62, "blue": 0.66}
LINE = {"red": 0.851, "green": 0.867, "blue": 0.886}

# ─────────────────────────────── чтение плана
doc = pymupdf.open("plan.pdf")
page = doc[0]
only_num = re.compile(r"^[\d.,\s]+$")
labels = []          # (регион, подпись)
for x0, y0, x1, y1, txt, _, _ in page.get_text("blocks"):
    for line in txt.split("\n"):
        t = line.strip()
        if not t or only_num.match(t):
            continue
        if any(s in t for s in ("remplanner", "Проект №", "Лист", "Мебель")):
            continue
        labels.append((region(x0), t))

left = [t for reg, t in labels if reg in ("left", "right")]
right = [t for reg, t in labels if reg == "block"]

# ─────────────────────────────── чтение штата
rows = [l.rstrip("\n").split("\t") for l in open("shtat.tsv", encoding="utf-8")]
data = [r + [""] * (12 - len(r)) for r in rows[1:] if any(c.strip() for c in r)]


# На схеме человек подписан не так, как в штатном источнике.
PLAN_ALIAS = {"Гладкова Алёна": "Гладкова Елена"}


def words(s):
    s = PLAN_ALIAS.get(s.strip(), s)
    s = s.lower().replace("ё", "е")
    s = re.sub(r"^\d+\.\s*", "", s)
    return re.findall(r"[а-яa-z]+", s)


def is_vac(r):
    return r[FIO].strip() == "Вакансия" or r[ST].strip() == "Вакансия"


staff = [r for r in data if r[FIO].strip() and r[FIO].strip() != "Вакансия"]
by_full = {tuple(sorted(words(r[FIO]))): r for r in staff}
by_word = defaultdict(list)
for r in staff:
    for w in words(r[FIO]):
        by_word[w].append(r)

seated, role_labels_left = {}, []
wing_named = Counter()        # места с фамилией по крыльям
wing_vac = Counter()          # места с подписью «Вакансия» по крыльям
for reg, t in labels:
    if reg == "block":
        continue
    ws = words(t)
    k = tuple(sorted(ws))
    r = None
    if k in by_full:
        r = by_full[k]
    elif len(ws) == 1 and len(by_word.get(ws[0], [])) == 1:
        r = by_word[ws[0]][0]
    if r is not None:
        seated[r[FIO].strip()] = t
        wing_named[reg] += 1
    else:
        role_labels_left.append(t)
        if t == "Вакансия":
            wing_vac[reg] += 1

WING_TITLE = {"left": "Остоженка · левое крыло", "right": "Остоженка · правое крыло"}
wing_seats = {w: wing_named[w] + wing_vac[w] for w in ("left", "right")}

vac_left = role_labels_left.count("Вакансия")
seats_left = len(seated) + vac_left
seats_right = len(right)
seats_total = seats_left + seats_right


def moscow(r):
    return r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")


active_msk = [r for r in staff if moscow(r) and not is_vac(r)]
vac_msk = [r for r in data if moscow(r) and is_vac(r)]
on_plan = set(seated)
no_seat = [r for r in active_msk if r[FIO].strip() not in on_plan]

# безымянные места справа против открытых вакансий штата
vac_pos = [(r[POS].strip(), r[DEP].strip()) for r in vac_msk]


def similar(a, b):
    wa, wb = set(words(a)), set(words(b))
    if not wa or not wb:
        return False
    return len(wa & wb) / max(len(wa), len(wb)) >= 0.5


right_matched = []
for role in right:
    hit = next((f"{p} ({d})" for p, d in vac_pos if similar(role, p)), "")
    right_matched.append((role, hit))

# ─────────────────────────────── строки
values, kind = [], []


def put(row, k):
    values.append([str(c) for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


put(["АНАЛИТИКА: ШТАТ ПРОТИВ ПЛАНА РАССАДКИ"], "title")
put([f"Источники: вкладка «Штат 21 09 26» и схема Plan №7565938 · "
     f"мест на схеме {seats_total} · подписи с фамилиями — {seats_left}, "
     f"только с должностью — {seats_right}"], "sub")
put([], "blank")

put(["1. Итоги"], "sect")
put(["Показатель", "Человек / мест", "", "", ""], "head")
put(["Мест на схеме — всего", seats_total], "grand")
put(["    подписаны фамилией", len(seated)], "sub_row")
put(["    подписаны «Вакансия»", vac_left], "sub_row")
put(["    подписаны только должностью", seats_right], "sub_row")
put(["Действующих сотрудников в штате (Москва, офис и гибрид)",
     len(active_msk)], "row")
put(["    из них получили место на схеме", len(active_msk) - len(no_seat)], "sub_row")
put(["    БЕЗ МЕСТА", len(no_seat)], "bad" if no_seat else "sub_row")
put(["Открытых вакансий в штате (Москва, офис и гибрид)", len(vac_msk)], "row")
put(["Свободных мест сверх действующего штата",
     seats_total - len(active_msk)], "row")
put([], "blank")

put(["2. Места по крыльям — посчитано по подписям на схеме"], "sect")
put(["Зона", "Всего мест", "С фамилией", "Подписано «Вакансия»", "Было в прежней аналитике"],
    "head")
OLD_CAP = {"right": 20, "left": 27}
for w in ("right", "left"):
    put([WING_TITLE[w], wing_seats[w], wing_named[w], wing_vac[w], OLD_CAP[w]], "row")
put(["Остоженка, 2 этаж — итого", sum(wing_seats.values()),
     sum(wing_named.values()), sum(wing_vac.values()), sum(OLD_CAP.values())], "total")
put(["Отдельный блок на схеме (без фамилий)", seats_right, 0, 0, "—"], "row")
put(["ВСЕГО МЕСТ НА СХЕМЕ", seats_total, len(seated), vac_left, "—"], "grand")
put(["Крылья определены сопоставлением со штатом: в восточной части схемы сидят "
     "люди с пометкой «Левое» (кабинеты Л1–Л4), в западной — «Правое» (П0–П7)",
     "", "", "", ""], "note")
put([], "blank")

put(["3. Кто из штата остался без места на схеме"], "sect")
put(["ФИО", "Отдел", "Должность", "Формат", "Руководитель"], "head")
if no_seat:
    for r in sorted(no_seat, key=lambda r: r[DEP].strip()):
        put([r[FIO].strip(), r[DEP].strip(), r[POS].strip(),
             r[FMT].strip(), r[MGR].strip() or "—"], "bad")
else:
    put(["Все сотрудники размещены", "", "", "", ""], "row")
put([], "blank")

put(["4. По отделам"], "sect")
put(["Отдел", "В штате", "На схеме", "Без места", "Вакансий в штате"], "head")
dep_all, dep_plan, dep_vac = Counter(), Counter(), Counter()
for r in active_msk:
    d = r[DEP].strip()
    dep_all[d] += 1
    if r[FIO].strip() in on_plan:
        dep_plan[d] += 1
for r in vac_msk:
    dep_vac[r[DEP].strip()] += 1
for d in sorted(set(dep_all) | set(dep_vac), key=lambda d: -(dep_all[d] + dep_vac[d])):
    miss = dep_all[d] - dep_plan[d]
    put([d, dep_all[d], dep_plan[d], miss, dep_vac[d]], "bad" if miss else "row")
put(["ИТОГО", sum(dep_all.values()), sum(dep_plan.values()),
     sum(dep_all.values()) - sum(dep_plan.values()), sum(dep_vac.values())], "grand")
put([], "blank")

put(["5. Места на схеме без фамилии"], "sect")
put(["Должность на схеме", "Есть такая вакансия в штате?", "", "", ""], "head")
for role, hit in sorted(right_matched, key=lambda x: (x[1] == "", x[0])):
    put([role, hit or "нет в штате", "", "", ""], "row" if hit else "amber")
put(["ИТОГО мест без фамилии", seats_right,
     f"совпало с вакансиями: {sum(1 for _, h in right_matched if h)}", "", ""], "grand")
put([], "blank")

put(["6. Открытые вакансии штата и место под них"], "sect")
put(["Должность", "Отдел", "Есть место на схеме?", "", ""], "head")
for r in sorted(vac_msk, key=lambda r: r[DEP].strip()):
    p = r[POS].strip()
    where = "подписано «Вакансия» слева" if p.lower().startswith("backend") and vac_left \
        else ("да, справа" if any(similar(role, p) for role in right) else "нет")
    put([p, r[DEP].strip(), where, "", ""],
        "row" if where != "нет" else "amber")
put(["ИТОГО вакансий", len(vac_msk), "", "", ""], "grand")

# ─────────────────────────────── запись
token = access_token(load_credentials())
meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,sheetId,gridProperties))")
props = next(x["properties"] for x in meta["sheets"] if x["properties"]["title"] == TAB)
sheet_id = props["sheetId"]

call(token, "POST", f"{SID}:batchUpdate", {"requests": [
    {"unmergeCells": {"range": {"sheetId": sheet_id}}},
    {"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"frozenRowCount": 0, "frozenColumnCount": 0}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
]})
call(token, "POST", f"{SID}/values/{quote(TAB)}:clear", {})
r = call(token, "PUT", f"{SID}/values/{quote(TAB)}?valueInputOption=RAW",
         {"values": values})
print("записано ячеек:", r.get("updatedCells"))

N = len(values)
meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,gridProperties))")
props = next(x["properties"] for x in meta["sheets"] if x["properties"]["title"] == TAB)
MAXROWS = props["gridProperties"]["rowCount"]
MAXCOLS = props["gridProperties"]["columnCount"]


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
for i, w in enumerate([360, 150, 300, 110, 200]):
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
                    verticalAlignment="MIDDLE", wrapStrategy="WRAP", padding=PAD)]
    elif k == "note":
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                    textFormat=font(9, italic=True, color=MUTED),
                    verticalAlignment="MIDDLE", wrapStrategy="WRAP", padding=PAD)]
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
    elif k == "amber":
        req.append(fmt(rng(i, i + 1), "userEnteredFormat.backgroundColor",
                       backgroundColor=AMBER))

for i, k in enumerate(kind):
    if k in ("row", "sub_row", "total", "grand", "bad", "amber"):
        req.append(fmt(rng(i, i + 1, 1, 2), "userEnteredFormat.horizontalAlignment",
                       horizontalAlignment="CENTER"))

start = None
for i, k in enumerate(kind + ["blank"]):
    if k in ("head", "row", "sub_row", "total", "grand", "bad", "amber"):
        start = i if start is None else start
    elif start is not None:
        req.append({"updateBorders": {
            "range": rng(start, i),
            "innerHorizontal": {"style": "SOLID", "color": LINE},
            "innerVertical": {"style": "SOLID", "color": LINE}}})
        start = None

call(token, "POST", f"{SID}:batchUpdate", {"requests": req})
print(f"оформление: {len(req)} операций, {N} строк")

back = call(token, "GET", f"{SID}/values/{quote(TAB)}").get("values", [])
bad = [i + 1 for i, w in enumerate(values)
       if [c.strip() for c in w]
       != [c.strip() for c in ((back[i] if i < len(back) else []) + [""] * NCOLS)][:NCOLS]]
assert not bad, f"расхождения в строках: {bad[:10]}"
print(f"сверка пройдена: {N} строк")
print(f"\nмест на схеме {seats_total} (именных {len(seated)}, «Вакансия» {vac_left}, "
      f"без фамилии {seats_right})")
print(f"действующих в штате (Москва) {len(active_msk)}, без места {len(no_seat)}")
for r in no_seat:
    print(f"   • {r[FIO].strip()} — {r[DEP].strip()}, {r[POS].strip()}")
