# -*- coding: utf-8 -*-
"""Новая вкладка: аналитика ФАКТИЧЕСКОЙ рассадки.

Источник один — вкладка «Штат 21 09 26», колонки «Офис (крыло)» и
«Кабинет». Это то, как люди сидят сейчас, а не как планируется.
Ни план-схема, ни ШТАТКА здесь не используются.
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
SRC = "Штат 21 09 26"
TAB = "Текущая рассадка"
NCOLS = 5

WING, ROOM, FIO, POS, DEP, ST, FMT, CITY, MGR = 1, 2, 3, 6, 7, 8, 9, 10, 11

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
raw = call(token, "GET", f"{SID}/values/{quote(SRC)}")["values"]
data = [r + [""] * (12 - len(r)) for r in raw[1:] if any(c.strip() for c in r)]


def vac(r):
    return r[FIO].strip() == "Вакансия" or r[ST].strip() == "Вакансия"


def wing_of(r):
    w = r[WING].strip()
    return "Левое" if w == "Левое" else ("Правое" if w.startswith("Правое") else w)


seated = [r for r in data if wing_of(r) in ("Левое", "Правое")]
no_seat = [r for r in data if wing_of(r) == "no"]
outside = [r for r in data if not wing_of(r)]
no_seat_people = [r for r in no_seat if not vac(r)]
no_seat_vac = [r for r in no_seat if vac(r)]
negotiation = [r for r in seated if r[ROOM].strip() == "Переговорная"]

rooms = defaultdict(list)
for r in seated:
    rooms[(wing_of(r), r[ROOM].strip())].append(r)

dep_rooms = defaultdict(Counter)
for r in seated:
    dep_rooms[r[DEP].strip()][r[ROOM].strip()] += 1

values, kind = [], []


def put(row, k):
    values.append([str(c) for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


put(["ТЕКУЩАЯ РАССАДКА — КАК СИДЯТ СЕЙЧАС"], "title")
put([f"Источник: вкладка «{SRC}», колонки «Офис (крыло)» и «Кабинет». "
     f"Фактическое размещение, не план переезда."], "sub")
put([], "blank")

put(["1. Итоги"], "sect")
put(["Показатель", "Человек", "", "", "Комментарий"], "head")
put(["Сидят в офисе на Остоженке", len(seated), "", "",
     f"{len(rooms)} кабинетов и зон"], "grand")
put(["    левое крыло", sum(1 for r in seated if wing_of(r) == "Левое"), "", "",
     "кабинеты Л1–Л4"], "sub_row")
put(["    правое крыло", sum(1 for r in seated if wing_of(r) == "Правое"), "", "",
     "кабинеты П0–П7 и переговорная"], "sub_row")
put(["    из них сидят в переговорной", len(negotiation), "", "",
     "переговорная занята под рабочие места"], "bad" if negotiation else "sub_row")
put(["Числятся в офисе, но места нет («no»)", len(no_seat_people), "", "",
     "оба на гибриде"], "bad" if no_seat_people else "row")
put(["Открытые вакансии без места", len(no_seat_vac), "", "",
     "места под наём не выделены"], "amber")
put(["Вне офисной рассадки", len(outside), "", "",
     "удалённые и другие города"], "row")
put(["ВСЕГО СТРОК В ШТАТЕ", len(data), "", "", ""], "grand")
put([], "blank")

put(["2. Загрузка кабинетов"], "sect")
put(["Кабинет", "Крыло", "Человек", "Отделов", "Кто сидит"], "head")


def room_key(item):
    (w, room), _ = item
    return (0 if w == "Левое" else 1, room == "Переговорная", room)


for (w, room), rs in sorted(rooms.items(), key=room_key):
    deps = Counter(r[DEP].strip() for r in rs)
    txt = ", ".join(f"{d} — {n}" for d, n in deps.most_common())
    put([room, w + " крыло", len(rs), len(deps), txt],
        "bad" if room == "Переговорная" else "row")
put(["ИТОГО", "", len(seated), "", f"{len(rooms)} кабинетов и зон"], "grand")
put([], "blank")

put(["3. Кто сидит в переговорной"], "sect")
put(["ФИО", "Отдел", "Должность", "Формат", "Руководитель"], "head")
for r in sorted(negotiation, key=lambda r: r[DEP].strip()):
    put([r[FIO].strip(), r[DEP].strip(), r[POS].strip(), r[FMT].strip(),
         r[MGR].strip() or "—"], "bad")
put(["ИТОГО", "", len(negotiation), "", "мест не хватает — люди в переговорной"],
    "grand")
put([], "blank")

put(["4. Насколько отдел разбросан по кабинетам"], "sect")
put(["Отдел", "Человек", "Кабинетов", "", "Где именно"], "head")
for dep in sorted(dep_rooms, key=lambda d: (-len(dep_rooms[d]), -sum(dep_rooms[d].values()))):
    c = dep_rooms[dep]
    where = ", ".join(f"{k} — {v}" for k, v in sorted(c.items()))
    put([dep, sum(c.values()), len(c), "", where], "amber" if len(c) >= 3 else "row")
put(["ИТОГО", len(seated), "", "", "жёлтым — отделы, разорванные на 3+ кабинета"],
    "grand")
put([], "blank")

put(["5. Числятся в офисе, но места нет"], "sect")
put(["ФИО / вакансия", "Отдел", "Должность", "Формат", "Руководитель"], "head")
for r in no_seat_people:
    put([r[FIO].strip(), r[DEP].strip(), r[POS].strip(), r[FMT].strip(),
         r[MGR].strip() or "—"], "bad")
for r in sorted(no_seat_vac, key=lambda r: r[DEP].strip()):
    put(["вакансия", r[DEP].strip(), r[POS].strip(), r[FMT].strip(),
         r[MGR].strip() or "—"], "amber")
put(["ИТОГО", "", len(no_seat), "", f"{len(no_seat_people)} человек + "
     f"{len(no_seat_vac)} вакансий"], "grand")

# ─────────────────────────── запись
tabs = get_tabs(token, SID)
if TAB not in tabs:
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
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}},
]})
call(token, "POST", f"{SID}/values/{quote(TAB)}:clear", {})
res = call(token, "PUT", f"{SID}/values/{quote(TAB)}?valueInputOption=RAW",
           {"values": values})
print("записано ячеек:", res.get("updatedCells"))

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
for i, w in enumerate([300, 150, 250, 100, 330]):
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
    if k in ("row", "sub_row", "grand", "bad", "amber"):
        req.append(fmt(rng(i, i + 1, 1, 4), "userEnteredFormat.horizontalAlignment",
                       horizontalAlignment="CENTER"))

req.append(fmt(rng(0, N, 2, 3), "userEnteredFormat.wrapStrategy",
               wrapStrategy="WRAP"))

start = None
for i, k in enumerate(kind + ["blank"]):
    if k in ("head", "row", "sub_row", "grand", "bad", "amber"):
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
print(f"\nсидят {len(seated)} (левое {sum(1 for r in seated if wing_of(r)=='Левое')}, "
      f"правое {sum(1 for r in seated if wing_of(r)=='Правое')}), "
      f"в переговорной {len(negotiation)}")
print(f"без места: {len(no_seat_people)} человек + {len(no_seat_vac)} вакансий")
print(f"вне рассадки: {len(outside)}")
