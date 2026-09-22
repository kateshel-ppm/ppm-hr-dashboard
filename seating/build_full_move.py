# -*- coding: utf-8 -*-
"""Вкладка «Рассадка — новый офис (полный переезд)».

Предложение рассадки при полном переезде в офис по плану с кабинетами
345–349 (фото плана от заказчика, 22.09.2026). Рабочие места считались
по стульям у столов на плане. Кухня-переговорная 34,17 м², переговорная П8,
лаунж 25,63 м² и коридоры за рабочие места не считаются — по условию
заказчика они остаются свободными.

Условия:
  * не переезжают офис-менеджеры (АХО), MAZE и ВЭД — остаются на Остоженке;
  * отделы не рвутся по кабинетам, руководители сидят со своими командами.
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Рассадка — новый офис (полный переезд)"
NCOLS = 5

FIO, GRADE, POS, DEP, ST, FMT, CITY, MGR = 3, 5, 6, 7, 8, 9, 10, 11
EXCLUDED = set()
# Не переезжают: офис-менеджеры, MAZE и ВЭД — остаются на Остоженке.
STAYING = {"АХО": "офис-менеджеры не переезжают",
           "MAZE": "MAZE не переезжает",
           "ВЭД": "ВЭД не переезжает"}

# (кабинет, площадь, мест по плану, где на плане)
ROOMS = [
    ("349", "41,04 м²", 14, "крайний кабинет, у лаунжа"),
    ("348", "87,46 м²", 28, "большой опенспейс, включая зону под переговорной П8"),
    ("347", "20,57 м²", 6,  "малый кабинет у лаунж-зоны"),
    ("346", "32,10 м²", 11, "кабинет у санузлов"),
    ("345а", "без номера", 8, "кабинет с перегородкой между 345 и 346, вход из 345"),
    ("345", "85,14 м²", 18, "опенспейс у кухни-переговорной"),
]
CAP = {r: n for r, _, n, _ in ROOMS}
AREA = {r: a for r, a, _, _ in ROOMS}
WHERE = {r: w for r, _, _, w in ROOMS}

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
grades = {}
for l in open("shtat_now.tsv", encoding="utf-8"):
    r = l.rstrip("\n").split("\t")
    if len(r) > 5 and r[3].strip():
        grades[r[3].strip()] = r[5].strip()

C_BY_TITLE = {"CTO", "HRD"}


def vac(r):
    return r[FIO].strip() == "Вакансия" or r[ST].strip() == "Вакансия"


def is_clevel(r):
    return ("level" in grades.get(r[FIO].strip(), "").lower()
            or r[POS].strip() in C_BY_TITLE
            or (vac(r) and r[POS].strip() == "Операционный директор"))


need_all = [r for r in src
            if r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")
            and r[DEP].strip() not in EXCLUDED]
staying = [r for r in need_all if r[DEP].strip() in STAYING]
need = [r for r in need_all if r[DEP].strip() not in STAYING]

clevel = [r for r in need if is_clevel(r)]
rest = defaultdict(list)
for r in need:
    if not is_clevel(r):
        rest[r[DEP].strip()].append(r)


def take(dep):
    out = rest[dep][:]
    rest[dep] = []
    return out


C = {r[POS].strip(): r for r in clevel}

# ─────────────────────────── распределение по кабинетам
PLAN = [
    # 348 — единый опенспейс ИТ: команда, CTO и директор по цифровым
    # технологиям (просьба заказчика посадить их вместе с ИТ), плюс AI.
    # Запас 5 мест — под рост самой большой команды.
    ("348", [C["Директор по цифровым технологиям"], C["CTO"]]
            + take("ИТ") + take("AI") + take("АУП")),
    # 345 — продукт с директором по продукту, ОКК и Забота (работают с
    # продуктом и клиентами), HR с HRD — рядом кухня-переговорная для встреч
    # и собеседований.
    ("345", [C["Директор по продукту"]] + take("Продукт") + take("ОКК")
            + take("Забота") + [C["HRD"]] + take("HR")),
    # 349 — маркетинг целиком с директором по маркетингу, плюс юристы.
    ("349", [C["Директор по маркетингу"]] + take("Маркетинг")
            + [C["Юрист"]] + take("ЮО")),
    # 346 — коммерческий блок: коммерческий директор, продажи, рефералы,
    # партнёры и PR с директором по стратегическим коммуникациям.
    ("346", [C["Коммерческий директор"]] + take("Продажи") + take("Рефералы")
            + take("Партнеры") + [C["Директор по стратегическим коммуникациям"]]
            + take("PR")),
    # 347 — финансы с финансовым директором, ровно 6 мест.
    ("347", [C["Финансовый директор"]] + take("Фин")),
    # 345а — кабинет с перегородкой: генеральный директор и вакансии
    # операционного директора и директора по орг развитию.
    ("345а", [C["Генеральный директор"], C["Операционный директор"],
              C["Директор по орг развитию"]]),
]

placed = {id(r) for _, rs in PLAN for r in rs}
lost = [f"{r[DEP].strip()}: {r[FIO].strip() or r[POS].strip()}"
        for r in need if id(r) not in placed]
assert not lost, f"без места: {lost}"
over = [(room, len(rs), CAP[room]) for room, rs in PLAN if len(rs) > CAP[room]]
assert not over, f"кабинет переполнен: {over}"

total_cap = sum(CAP.values())
seated = sum(len(rs) for _, rs in PLAN)
assert seated == len(need), "кто-то потерялся"

values, kind = [], []


def put(row, k):
    values.append([str(c) for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


def who(r):
    return "вакансия" if vac(r) else r[FIO].strip()


put(["РАССАДКА — НОВЫЙ ОФИС, ПОЛНЫЙ ПЕРЕЕЗД (кабинеты 345–349)"], "title")
put([f"Рабочих мест по плану {total_cap} (по стульям у столов). Переезжает {seated}: "
     f"{sum(1 for r in need if not vac(r))} человек + {sum(1 for r in need if vac(r))} вакансий. "
     f"Свободно {total_cap - seated}. Офис-менеджеры, MAZE и ВЭД остаются на Остоженке. "
     f"Кухня-переговорная, переговорная П8 и лаунж за рабочие места не считаются."], "sub")
put([], "blank")

put(["1. Итоги"], "sect")
put(["Показатель", "Мест", "", "", "Комментарий"], "head")
put(["Рабочих мест в новом офисе", total_cap, "", "",
     " + ".join(f"{r} — {n}" for r, _, n, _ in ROOMS)], "grand")
put(["Переезжает", seated, "", "",
     f"{sum(1 for r in need if not vac(r))} человек + {sum(1 for r in need if vac(r))} вакансий"], "grand")
put(["Свободно (резерв)", total_cap - seated, "", "",
     " · ".join(f"{room} — {CAP[room] - len(rs)}" for room, rs in PLAN if CAP[room] > len(rs))], "good")
put(["Не переезжают", len(staying), "", "",
     " · ".join(f"{d}: " + ", ".join(r[FIO].strip() for r in staying if r[DEP].strip() == d)
                for d in STAYING)], "grey")
put(["Не занимаем", 0, "", "",
     "кухня-переговорная 34,17 м², переговорная П8, лаунж 25,63 м²"], "grey")
put([], "blank")

put(["2. Кабинеты — кто где"], "sect")
put(["Кабинет", "Площадь", "Мест", "Занято", "Отделы и должности"], "head")
for room, rs in PLAN:
    by_dep = defaultdict(list)
    for r in rs:
        by_dep[r[DEP].strip()].append(r[POS].strip() + (" (вакансия)" if vac(r) else ""))
    parts = [f"{d} ({len(ps)}): " + ", ".join(ps)
             for d, ps in sorted(by_dep.items(), key=lambda x: -len(x[1]))]
    free = CAP[room] - len(rs)
    txt = " · ".join(parts) + (f"   — свободно {free}" if free else "")
    put([room, AREA[room], CAP[room], len(rs), txt], "row" if free == 0 else "good")
put(["ИТОГО", "", total_cap, seated, f"свободно {total_cap - seated}"], "grand")
put([], "blank")

put(["3. Где какой кабинет на плане"], "sect")
put(["Кабинет", "Площадь", "Мест", "", "Ориентир"], "head")
for room, area, n, where in ROOMS:
    put([room, area, n, "", where], "row")
put([], "blank")

put(["4. Поимённо"], "sect")
put(["Кабинет", "Отдел", "ФИО", "Должность", "Руководитель"], "head")
for room, rs in PLAN:
    for r in rs:
        put([room, r[DEP].strip(), who(r), r[POS].strip(), r[MGR].strip() or "—"],
            "amber" if vac(r) else "row")
put(["ИТОГО", "", seated, "", ""], "grand")
put([], "blank")

put(["5. Остаются на Остоженке"], "sect")
put(["Отдел", "ФИО", "Должность", "", "Почему"], "head")
for r in staying:
    put([r[DEP].strip(), who(r), r[POS].strip(), "", STAYING[r[DEP].strip()]], "grey")
put(["ИТОГО", len(staying), "", "", ""], "grand")

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
