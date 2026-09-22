# -*- coding: utf-8 -*-
"""Новая вкладка: предложение рассадки с освобождённой переговорной.

Ограничения заказчика:
  * переговорная перестаёт быть рабочей зоной — минус 7 мест;
  * C-level и офис-менеджеры остаются в текущем офисе;
  * остальное распределяем так, чтобы отделы не рвались по кабинетам.

Вместимость кабинетов взята по факту из вкладки «Штат 21 09 26»
(сколько людей там сидит сейчас). Состав — объединённый источник:
люди из «ШТАТКИ», вакансии из «Штат 21 09 26».
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Рассадка — предложение"
NCOLS = 5

FIO, GRADE, POS, DEP, ST, FMT, CITY, MGR = 3, 5, 6, 7, 8, 9, 10, 11
# MAZE возвращён в рассадку по решению заказчика и сидит отдельно в П7.
# ВЭД по-прежнему вне рассадки.
EXCLUDED = {"ВЭД"}
NEW_OFFICE_CAP = 41

ROOMS = [("Л1", "левое", 2), ("Л2", "левое", 5), ("Л3", "левое", 11), ("Л4", "левое", 11),
         ("П0", "правое", 2), ("П1", "правое", 1), ("П2", "правое", 1), ("П3", "правое", 1),
         ("П4", "правое", 1), ("П5", "правое", 2), ("П6", "правое", 8), ("П7", "правое", 6)]
CAP = {r: n for r, _, n in ROOMS}

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
# грейд C-level живёт в исходной вкладке переезда
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


need = [r for r in src
        if r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")
        and r[DEP].strip() not in EXCLUDED]

clevel = [r for r in need if is_clevel(r)]
rest = defaultdict(list)
for r in need:
    if not is_clevel(r):
        rest[r[DEP].strip()].append(r)


def take(dep, n=None):
    out = rest[dep][:n] if n else rest[dep][:]
    rest[dep] = rest[dep][len(out):]
    return out


def take_named(dep, names):
    """Забирает из отдела конкретных людей (или вакансию по должности)."""
    out = [r for r in rest[dep]
           if r[FIO].strip() in names or r[POS].strip() in names]
    missing = names - {r[FIO].strip() for r in out} - {r[POS].strip() for r in out}
    assert not missing, f"в отделе {dep} не найдены: {missing}"
    rest[dep] = [r for r in rest[dep] if r not in out]
    return out


def by_title(rs, title):
    return next(r for r in rs if r[POS].strip() == title)


C = {r[POS].strip(): r for r in clevel}

# ─────────────────────────── распределение по кабинетам
PLAN = [
    ("П1", [C["Генеральный директор"]]),
    ("П2", [C["Директор по цифровым технологиям"]]),
    ("П3", [C["Коммерческий директор"]]),
    # П4 освобождается: CMO уходит к своей команде в Л4
    ("П4", []),
    ("П5", [C["Директор по продукту"], C["CTO"]]),
    ("П0", take("АХО")),
    # П6 освобождается: весь маркетинг собран в Л4
    ("П6", []),
    # П7: MAZE вдвоём плюс две директорские вакансии — по орг развитию
    # и операционная. Других свободных мест в правом крыле нет.
    ("П7", take("MAZE") + [C["Директор по орг развитию"],
                           C["Операционный директор"]]),
    # Л1: CFO с финансовым менеджером — место под операционного директора
    # отдано, чтобы в Л2 поместилась Смелова (её вернули в этот кабинет).
    ("Л1", [C["Финансовый директор"]] + take_named("Фин", {"Домокурова Юлия"})),
    ("Л2", take_named("HR", {"Смелова Наталья"}) + take("Фин")),
    # Л3 — PR, партнёры, юристы (переехали сюда из Л4) и руководитель
    # реферальной программы: его вернули на Остоженку, это единственное
    # свободное место в левом крыле.
    ("Л3", [C["Директор по стратегическим коммуникациям"]] + take("PR")
            + take("Партнеры") + [C["Юрист"]] + take("ЮО")
            + take_named("Рефералы", {"Коломиец Даниил"})),
    # Л4 — весь маркетинг вместе с директором по маркетингу, ровно 11 мест
    ("Л4", [C["Директор по маркетингу"]] + take("Маркетинг")),
]

# C-level по общему правилу остаётся, но эти двое переезжают вместе с HR —
# отдельное указание заказчика, важнее общего правила.
CLEVEL_MOVING = {"HRD"}

placed = {id(r) for _, rs in PLAN for r in rs}
lost = [r[POS].strip() for r in clevel
        if id(r) not in placed and r[POS].strip() not in CLEVEL_MOVING]
assert not lost, f"C-level без кабинета: {lost}"

stay = [r for _, rs in PLAN for r in rs]
move = [r for r in need if id(r) not in placed]

over = [(room, len(rs), CAP[room]) for room, rs in PLAN if len(rs) > CAP[room]]
assert not over, f"кабинет переполнен: {over}"
assert len(stay) + len(move) == len(need), "кто-то потерялся"

stay_cnt, move_cnt = len(stay), len(move)
cur_cap = sum(CAP.values())

values, kind = [], []


def put(row, k):
    values.append([str(c) for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


def who(r):
    return (r[FIO].strip() or "вакансия") if not vac(r) else "вакансия"


put(["ПРЕДЛОЖЕНИЕ РАССАДКИ — ПЕРЕГОВОРНАЯ СВОБОДНА"], "title")
put([f"Текущий офис без переговорной — {cur_cap} мест. Всего нужно {len(need)}: "
     f"остаётся {stay_cnt}, переезжает {move_cnt}. "
     f"C-level и офис-менеджеры остаются (кроме HR-руководства), MAZE занимает П7 отдельно, ВЭД вне рассадки."], "sub")
put([], "blank")

put(["1. Итоги и проверка ограничений"], "sect")
put(["Показатель", "Мест", "", "", "Комментарий"], "head")
put(["Текущий офис — вместимость без переговорной", cur_cap, "", "",
     "левое 29 + правое 22"], "grand")
put(["    остаётся в текущем офисе", stay_cnt, "", "",
     f"свободно {cur_cap - stay_cnt}"], "row")
put(["Переезжает в новый офис", move_cnt, "", "",
     f"из {NEW_OFFICE_CAP} мест, свободно {NEW_OFFICE_CAP - move_cnt}"], "grand")
put(["ВСЕГО МЕСТ НУЖНО", len(need), "", "",
     f"{sum(1 for r in need if not vac(r))} человек + "
     f"{sum(1 for r in need if vac(r))} вакансий"], "grand")
put(["Переговорная", 0, "", "", "освобождена, рабочих мест нет"], "good")
put(["MAZE — отдельный кабинет П7", len([r for r in need if r[DEP].strip()=='MAZE']),
     "", "", "плюс вакансии директора по орг развитию и операционного, свободно 2"], "good")
put(["C-level в текущем офисе", len(clevel) - len(CLEVEL_MOVING), "", "",
     "кроме HRD — она с HR в новом офисе"], "good")
put(["Офис-менеджеры в текущем офисе", 2, "", "", "П0, у входа"], "good")
put([], "blank")

put(["2. Текущий офис — что в каком кабинете"], "sect")
put(["Кабинет", "Крыло", "Мест", "Занято", "Отделы и должности"], "head")
for room, rs in sorted(PLAN, key=lambda x: (x[0][0] != "Л", x[0])):
    by_dep = defaultdict(list)
    for r in rs:
        by_dep[r[DEP].strip()].append(r[POS].strip()
                                      + (" (вакансия)" if vac(r) else ""))
    parts = [f"{d} ({len(ps)}): " + ", ".join(ps)
             for d, ps in sorted(by_dep.items(), key=lambda x: -len(x[1]))]
    free = CAP[room] - len(rs)
    txt = " · ".join(parts) + (f"   — свободно {free}" if free else "")
    put([room, f"{dict((r, w) for r, w, _ in ROOMS)[room]} крыло", CAP[room],
         len(rs), txt], "row" if free == 0 else "good")
put(["Переговорная", "правое крыло", 0, 0, "освобождена"], "grey")
put(["ИТОГО", "", cur_cap, stay_cnt, f"свободно {cur_cap - stay_cnt}"], "grand")
put([], "blank")

put(["3. Текущий офис — поимённо"], "sect")
put(["Кабинет", "Отдел", "ФИО", "Должность", "Статус"], "head")
for room, rs in sorted(PLAN, key=lambda x: (x[0][0] != "Л", x[0])):
    for r in rs:
        put([room, r[DEP].strip(), who(r), r[POS].strip(),
             "вакансия" if vac(r) else "работает"], "amber" if vac(r) else "row")
put(["ИТОГО", "", stay_cnt, "", ""], "grand")
put([], "blank")

put(["4. Что переводится в новый офис"], "sect")
put(["Отдел", "Человек", "Вакансий", "Всего мест", "Должности"], "head")
mg = defaultdict(list)
for r in move:
    mg[r[DEP].strip()].append(r)
for dep in sorted(mg, key=lambda d: -len(mg[d])):
    rs = mg[dep]
    p = sum(1 for r in rs if not vac(r))
    titles = Counter(r[POS].strip() for r in rs)
    txt = ", ".join(f"{t}×{n}" if n > 1 else t for t, n in titles.most_common())
    put([dep, p, len(rs) - p, len(rs), txt], "row")
put(["ИТОГО", sum(1 for r in move if not vac(r)),
     sum(1 for r in move if vac(r)), move_cnt,
     f"из {NEW_OFFICE_CAP} мест нового офиса"], "grand")
put([], "blank")

put(["5. Новый офис — поимённо"], "sect")
put(["Отдел", "ФИО", "Должность", "Статус", "Руководитель"], "head")
for dep in sorted(mg, key=lambda d: -len(mg[d])):
    for r in sorted(mg[dep], key=lambda r: (vac(r), r[FIO].strip())):
        put([dep, who(r), r[POS].strip(), "вакансия" if vac(r) else "работает",
             r[MGR].strip() or "—"], "amber" if vac(r) else "row")
put(["ИТОГО", move_cnt, "", "", ""], "grand")

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
print(f"\nостаётся {stay_cnt} из {cur_cap}, переезжает {move_cnt} из {NEW_OFFICE_CAP}")
for dep in sorted(mg, key=lambda d: -len(mg[d])):
    print(f"   переезд: {dep:<10} {len(mg[dep])}")
