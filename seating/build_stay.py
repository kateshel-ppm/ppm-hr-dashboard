# -*- coding: utf-8 -*-
"""Вкладка «Остоженка — кто остаётся»: рассадка не переезжающих по крыльям.

Состав — те, кого `stay_rules.py` оставляет в варианте 2 (маркетинг остаётся).
Кабинеты и ёмкости — как в «Рассадка — предложение»: переговорная свободна,
левое крыло 29 мест, правое 22.

Логика та же, что в принятом предложении: C-level по одному в кабинетах
правого крыла, офис-менеджеры у входа (П0), MAZE отдельно в П7, Смелова с
главбухом в Л2, PR, партнёры, юристы и рефералы в Л3, маркетинг и продажи в Л4,
директор по маркетингу отдельно в П2.
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402
from stay_rules import FIO, GRADE, POS, DEP, ST, FMT, CITY, MGR, rules, vac  # noqa: E402,F401

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Остоженка — кто остаётся"
NCOLS = 5

ROOMS = [("Л1", "левое", 2), ("Л2", "левое", 5), ("Л3", "левое", 11), ("Л4", "левое", 11),
         ("П0", "правое", 2), ("П1", "правое", 1), ("П2", "правое", 1), ("П3", "правое", 1),
         ("П4", "правое", 1), ("П5", "правое", 2), ("П6", "правое", 8), ("П7", "правое", 6)]
CAP = {r: n for r, _, n in ROOMS}
WING = {r: w for r, w, _ in ROOMS}

NAVY = {"red": 0.114, "green": 0.180, "blue": 0.333}
BLUE = {"red": 0.180, "green": 0.459, "blue": 0.714}
PALE = {"red": 0.867, "green": 0.922, "blue": 0.969}
AMBER = {"red": 1.0, "green": 0.949, "blue": 0.800}
GREEN = {"red": 0.886, "green": 0.945, "blue": 0.898}
GREY = {"red": 0.953, "green": 0.953, "blue": 0.953}
WHITE = {"red": 1, "green": 1, "blue": 1}
INK = {"red": 0.114, "green": 0.180, "blue": 0.333}
MUTED = {"red": 0.60, "green": 0.62, "blue": 0.66}
LINE = {"red": 0.851, "green": 0.867, "blue": 0.886}

# ─────────────────────────── состав
src = [l.rstrip("\n").split("\t") for l in open("shtat.tsv", encoding="utf-8")]
src = [r + [""] * (12 - len(r)) for r in src[1:] if any(c.strip() for c in r)]

STAYING, STAY_NAMES, STAY_VAC, stays, why_stays = rules(marketing_stays=True)

need = [r for r in src
        if r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")
        and stays(r)]
missing = STAY_NAMES - {r[FIO].strip() for r in need}
assert not missing, f"не найдены в штате: {missing}"

by_dep = defaultdict(list)
for r in need:
    by_dep[r[DEP].strip()].append(r)


def take(dep):
    out = by_dep[dep][:]
    by_dep[dep] = []
    return out


def take_named(dep, names):
    out = [r for r in by_dep[dep] if r[FIO].strip() in names or r[POS].strip() in names]
    got = {r[FIO].strip() for r in out} | {r[POS].strip() for r in out}
    assert not names - got, f"в отделе {dep} не найдены: {names - got}"
    by_dep[dep] = [r for r in by_dep[dep] if r not in out]
    return out


# ─────────────────────────── распределение по кабинетам
# Директор по маркетингу — отдельно в П2 (указание заказчика), команда в Л4.
cmo = take_named("Маркетинг", {"Директор по маркетингу"})
PLAN = [
    ("Л1", take_named("Фин", {"Финансовый директор", "Домокурова Юлия"})),
    ("Л2", take_named("HR", {"Смелова Наталья"}) + take("Фин")),
    # Л3 — PR с директором по стратегическим коммуникациям (и Ермохин),
    # партнёры, юристы, руководитель рефералов — как в принятом предложении.
    ("Л3", take("PR") + take("Партнеры") + take("ЮО") + take("Рефералы")),
    # Л4 — маркетинг без директора плюс руководитель продаж карточного продукта.
    ("Л4", take("Маркетинг") + take("Продажи")),
    ("П0", take("АХО")),
    ("П1", take_named("АУП", {"Генеральный директор"})),
    ("П2", cmo),
    ("П3", take_named("АУП", {"Коммерческий директор"})),
    # П4 — казначей ВЭД, отдельный кабинет.
    ("П4", take("ВЭД")),
    ("П5", []),
    ("П6", []),
    # П7 — MAZE вдвоём плюс вакансия директора по орг развитию.
    ("П7", take("MAZE") + take_named("HR", {"Директор по орг развитию"})),
]

left = [r for d, rs in by_dep.items() for r in rs]
assert not left, "без места: " + ", ".join(f"{r[DEP]}: {r[FIO] or r[POS]}" for r in left)
over = [(room, len(rs), CAP[room]) for room, rs in PLAN if len(rs) > CAP[room]]
assert not over, f"кабинет переполнен: {over}"
seated = sum(len(rs) for _, rs in PLAN)
assert seated == len(need), "кто-то потерялся"
total_cap = sum(CAP.values())


def wing_stats(w):
    cap = sum(n for r, ww, n in ROOMS if ww == w)
    used = sum(len(rs) for room, rs in PLAN if WING[room] == w)
    return cap, used


values, kind = [], []


def put(row, k):
    values.append([str(c) for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


def who(r):
    return "вакансия" if vac(r) else r[FIO].strip()


lc, lu = wing_stats("левое")
rc, ru = wing_stats("правое")

put(["ОСТОЖЕНКА — КТО ОСТАЁТСЯ (после переезда ИТ и продукта в новый офис)"], "title")
put([f"Остаются {seated}: {sum(1 for r in need if not vac(r))} человек + "
     f"{sum(1 for r in need if vac(r))} вакансий. Мест без переговорной {total_cap}, "
     f"свободно {total_cap - seated}. Левое крыло {lu}/{lc}, правое {ru}/{rc}. "
     f"Состав — вариант «Рассадка — новый офис (без маркетинга)»."], "sub")
put([], "blank")

put(["1. Итоги по крыльям"], "sect")
put(["Крыло", "Мест", "Занято", "Свободно", "Кабинеты"], "head")
put(["Левое крыло", lc, lu, lc - lu,
     " · ".join(f"{room} {len(rs)}/{CAP[room]}" for room, rs in PLAN if WING[room] == "левое")],
    "row" if lc == lu else "good")
put(["Правое крыло", rc, ru, rc - ru,
     " · ".join(f"{room} {len(rs)}/{CAP[room]}" for room, rs in PLAN if WING[room] == "правое")],
    "row" if rc == ru else "good")
put(["Переговорная", 0, 0, 0, "свободна, рабочих мест нет"], "grey")
put(["ИТОГО", total_cap, seated, total_cap - seated, ""], "grand")
put([], "blank")

for wing, title in (("левое", "2. Левое крыло"), ("правое", "3. Правое крыло")):
    put([title], "sect")
    put(["Кабинет", "Мест", "Занято", "Свободно", "Отделы и должности"], "head")
    for room, rs in PLAN:
        if WING[room] != wing:
            continue
        bd = defaultdict(list)
        for r in rs:
            bd[r[DEP].strip()].append(r[POS].strip() + (" (вакансия)" if vac(r) else ""))
        parts = [f"{d} ({len(ps)}): " + ", ".join(ps)
                 for d, ps in sorted(bd.items(), key=lambda x: -len(x[1]))]
        free = CAP[room] - len(rs)
        put([room, CAP[room], len(rs), free, " · ".join(parts) or "свободен"],
            "row" if free == 0 else "good")
    c, u = wing_stats(wing)
    put(["ИТОГО", c, u, c - u, ""], "grand")
    put([], "blank")

put(["4. Поимённо"], "sect")
put(["Кабинет", "Отдел", "ФИО", "Должность", "Руководитель"], "head")
for room, rs in PLAN:
    for r in rs:
        put([room, r[DEP].strip(), who(r), r[POS].strip(), r[MGR].strip() or "—"],
            "amber" if vac(r) else "row")
put(["ИТОГО", "", seated, "", ""], "grand")

# ─────────────────────────── запись
if TAB not in get_tabs(token := access_token(load_credentials()), SID):
    call(token, "POST", f"{SID}:batchUpdate",
         {"requests": [{"addSheet": {"properties": {"title": TAB}}}]})
    print(f"создана вкладка «{TAB}»")
meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,sheetId,gridProperties))")
props = next(x["properties"] for x in meta["sheets"] if x["properties"]["title"] == TAB)
sheet_id = props["sheetId"]
call(token, "POST", f"{SID}:batchUpdate", {"requests": [
    {"unmergeCells": {"range": {"sheetId": sheet_id}}},
    {"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"frozenRowCount": 0, "frozenColumnCount": 0}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}}]})
call(token, "POST", f"{SID}/values/{quote(TAB)}:clear", {})
res = call(token, "PUT", f"{SID}/values/{quote(TAB)}?valueInputOption=RAW",
           {"values": values})
print("записано ячеек:", res.get("updatedCells"))

N = len(values)
meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,gridProperties))")
props = next(x["properties"] for x in meta["sheets"] if x["properties"]["title"] == TAB)
MAXROWS, MAXCOLS = (props["gridProperties"]["rowCount"],
                    props["gridProperties"]["columnCount"])


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
    req.append({"updateBorders": {"range": rng(0, TAIL, NCOLS, MAXCOLS),
                                  "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
                                  "left": {"style": "NONE"}, "right": {"style": "NONE"},
                                  "innerHorizontal": {"style": "NONE"},
                                  "innerVertical": {"style": "NONE"}}})
if N < TAIL:
    req.append({"updateBorders": {"range": rng(N, TAIL, 0, MAXCOLS),
                                  "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
                                  "left": {"style": "NONE"}, "right": {"style": "NONE"},
                                  "innerHorizontal": {"style": "NONE"},
                                  "innerVertical": {"style": "NONE"}}})
for i, w in enumerate([150, 115, 195, 320, 560]):
    req.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                  "startIndex": i, "endIndex": i + 1},
        "properties": {"pixelSize": w}, "fields": "pixelSize"}})

STYLE = {"grand": (NAVY, font(11, bold=True, color=WHITE)),
         "good": (GREEN, None), "amber": (AMBER, None), "grey": (GREY, None)}
for i, k in enumerate(kind):
    if k == "title":
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                    textFormat=font(18, bold=True, color=INK),
                    verticalAlignment="MIDDLE", padding=PAD)]
    elif k == "sub":
        req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                fmt(rng(i, i + 1), FULL, backgroundColor=WHITE,
                    textFormat=font(10, color=MUTED), verticalAlignment="MIDDLE",
                    wrapStrategy="WRAP", padding=PAD)]
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
    elif k in STYLE:
        bg, f = STYLE[k]
        if f:
            req.append(fmt(rng(i, i + 1), FULL, backgroundColor=bg, textFormat=f,
                           verticalAlignment="MIDDLE", padding=PAD))
        else:
            req.append(fmt(rng(i, i + 1), "userEnteredFormat.backgroundColor",
                           backgroundColor=bg))

for i, k in enumerate(kind):
    if k in ("row", "grand", "good", "amber", "grey"):
        req.append(fmt(rng(i, i + 1, 1, 4), "userEnteredFormat.horizontalAlignment",
                       horizontalAlignment="CENTER"))
req.append(fmt(rng(0, N, 3, 4), "userEnteredFormat.horizontalAlignment",
               horizontalAlignment="LEFT"))
req.append(fmt(rng(0, N, 2, 5), "userEnteredFormat.wrapStrategy", wrapStrategy="WRAP"))

start = None
for i, k in enumerate(kind + ["blank"]):
    if k in ("head", "row", "grand", "good", "amber", "grey"):
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
