# -*- coding: utf-8 -*-
"""Собирает рассадку из «Штат 21 09 26», пишет её во вкладку и оформляет."""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SPREADSHEET = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Рассадка по отделам 21.09.26"
NCOLS = 9

FIO, GRADE, POS, DEP, VAC, FMT, CITY, MGR = 3, 5, 6, 7, 8, 9, 10, 11

# ─────────────────────────────────────────────────────── палитра
NAVY = {"red": 0.114, "green": 0.180, "blue": 0.333}   # #1D2E55 шапка
BLUE = {"red": 0.180, "green": 0.459, "blue": 0.714}   # #2E75B6 зоны
PALE = {"red": 0.867, "green": 0.922, "blue": 0.969}   # #DDEBF7 блоки
AMBER = {"red": 1.0, "green": 0.949, "blue": 0.800}    # #FFF2CC вакансии
GREY = {"red": 0.953, "green": 0.953, "blue": 0.953}   # #F3F3F3 резерв
WHITE = {"red": 1, "green": 1, "blue": 1}
INK = {"red": 0.114, "green": 0.180, "blue": 0.333}
MUTED = {"red": 0.533, "green": 0.553, "blue": 0.596}
LINE = {"red": 0.851, "green": 0.867, "blue": 0.886}

# ─────────────────────────────────────────────────────── данные
rows = [l.rstrip("\n").split("\t") for l in open("shtat.tsv", encoding="utf-8")]
data = [r + [""] * (12 - len(r)) for r in rows[1:] if any(c.strip() for c in r)]


def needs_seat(r):
    return r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")


def is_vacancy(r):
    return r[FIO].strip() == "Вакансия" or r[VAC].strip() == "Вакансия"


# Отделы, исключённые из рассадки по решению заказчика
EXCLUDED_DEPS = {"MAZE", "ВЭД"}

pool = {}
excluded = []
for r in data:
    if not needs_seat(r):
        continue
    dep = r[DEP].strip()
    if dep in EXCLUDED_DEPS:
        excluded.append(r)
        continue
    r[DEP] = dep
    pool.setdefault(dep, []).append(r)

used = []


def take(dep, match=None, exclude=None):
    out = []
    for r in pool.get(dep, []):
        if r in used:
            continue
        name = r[FIO].strip()
        if match and name not in match:
            continue
        if exclude and name in exclude:
            continue
        out.append(r)
    used.extend(out)
    return out


NEW, LEFT, RIGHT = "Новый офис", "Остоженка · левое крыло", "Остоженка · правое крыло"
CAPACITY = {NEW: 41, LEFT: 27, RIGHT: 20}

PLAN = [
    (NEW, [
        # CDO и CTO сидят вместе с командой в общем опенспейсе ИТ
        ("ИТ — опенспейс", take("АУП", match={"Печенев Андрей"})
                           + take("ИТ", match={"Шияфетдинов Дамир"})
                           + take("ИТ")),
        ("AI", take("AI")),
        ("Продукт — опенспейс", take("Продукт", exclude={"Головко Илья"})),
        # Смелова сидит с главным бухгалтером в правом крыле, см. ниже
        ("HR", take("HR", exclude={"Смелова Наталья"})),
        ("Забота / Качество", take("Забота") + take("ОКК")),
    ]),
    (LEFT, [
        ("Кабинеты", take("АУП") + take("Маркетинг", match={"Носенко Вячеслав"})
                     + take("Продукт", match={"Головко Илья"})),
        ("Малый опенспейс", take("ЮО") + take("Партнеры")),
        ("Опенспейс", take("PR") + take("Рефералы") + take("Продажи")
                      + take("Маркетинг", match={"Калабин Илья", "Борецкий Илья", "Барбашов Александр"})),
        ("Ресепшн / АХО", take("АХО")),
    ]),
    (RIGHT, [
        ("Кабинет", take("Фин", match={"Зеленцов Александр"})),
        # руководитель отдела кадров сидит вместе с главным бухгалтером
        ("Финансовый опенспейс", take("Фин") + take("HR", match={"Смелова Наталья"})),
        ("Большой опенспейс — маркетинг", take("Маркетинг")),
    ]),
]

allocated = [r for _, blocks in PLAN for _, rs in blocks for r in rs]
everyone = [r for rs in pool.values() for r in rs]
assert len(allocated) == len(set(map(id, allocated))), "дубли мест"
missing = [r for r in everyone if r not in allocated]
assert not missing, f"не рассажены: {[(r[FIO], r[DEP]) for r in missing]}"

people = sum(1 for r in allocated if not is_vacancy(r))
vacs = len(allocated) - people

# ─────────────────────────────────────────────────────── строки + разметка
values, kind = [], []          # kind: title/sub/blank/head/zone/block/row/vac/res


def put(row, k):
    values.append(row + [""] * (NCOLS - len(row)))
    kind.append(k)


put(["РАССАДКА ПО ОТДЕЛАМ"], "title")
put([f"Источники: «ШТАТКА» (состав) + вакансии из «Штат 21 09 26» · {len(allocated)} мест = "
     f"{people} сотрудников + {vacs} вакансий · только Москва (офис и гибрид) · "
     f"без отделов {', '.join(sorted(EXCLUDED_DEPS))}"], "sub")
put([], "blank")
put(["№", "Офис / зона", "Блок", "Отдел", "ФИО", "Должность",
     "Прямой руководитель", "Формат", "Статус"], "head")

# Резерв: ровно одно место на отдел, в том блоке, где у отдела больше всего мест.
dept_block = {}
for zone, blocks in PLAN:
    for block, rs in blocks:
        for r in rs:
            dept_block.setdefault(r[DEP].strip(), Counter())[(zone, block)] += 1
RESERVE_AT = defaultdict(list)
for dep, counts in dept_block.items():
    RESERVE_AT[counts.most_common(1)[0][0]].append(dep)

seat = 0
for zone, blocks in PLAN:
    cap = CAPACITY[zone]
    taken = sum(len(rs) for _, rs in blocks)
    reserve = sum(len(RESERVE_AT[(zone, b)]) for b, _ in blocks)
    free = cap - taken - reserve
    tail = f"свободно {free}" if free >= 0 else f"НЕ ХВАТАЕТ {-free}"
    put([f"{zone}      занято {taken}   резерв {reserve}   из {cap}      {tail}"], "zone")
    for block, rs in blocks:
        res_deps = sorted(RESERVE_AT[(zone, block)])
        put([f"{block}  ·  {len(rs)}" + (f"  + резерв {len(res_deps)}" if res_deps else "")],
            "block")
        for r in rs:
            seat += 1
            vac = is_vacancy(r)
            # у вакансии с названным кандидатом (CTO) показываем имя, а не прочерк
            name = r[FIO].strip()
            put([seat, zone, block, r[DEP].strip(),
                 name if name and name != "Вакансия" else "—",
                 r[POS].strip(), r[MGR].strip() or "—", r[FMT].strip(),
                 "вакансия" if vac else "работает"], "vac" if vac else "row")
        for dep in res_deps:
            seat += 1
            put([seat, zone, block, dep, "—", f"— резерв отдела {dep} —", "—", "—",
                 "резерв"], "res")

# ─────────────────────────────────────────────────────── запись
token = access_token(load_credentials())
sheet_id = get_tabs(token, SPREADSHEET)[TAB]

# ВАЖНО: слияния снимаем ДО записи значений. Если писать в объединённый
# диапазон, Sheets сохраняет только его верхнюю левую ячейку, а остальные
# значения молча теряются — строка выглядит пустой после разъединения.
call(token, "POST", f"{SPREADSHEET}:batchUpdate",
     {"requests": [{"unmergeCells": {"range": {"sheetId": sheet_id}}}]})

call(token, "POST", f"{SPREADSHEET}/values/{quote(TAB)}:clear", {})
res = call(token, "PUT", f"{SPREADSHEET}/values/{quote(TAB)}?valueInputOption=RAW",
           {"values": values})
print("записано ячеек:", res.get("updatedCells"))

# ─────────────────────────────────────────────────────── оформление
N = len(values)


def rng(r0, r1, c0=0, c1=NCOLS):
    return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
            "startColumnIndex": c0, "endColumnIndex": c1}


def cell(fields, **fmt):
    return {"repeatCell": {"range": fmt.pop("range"),
                           "cell": {"userEnteredFormat": fmt},
                           "fields": fields}}


def text(size=10, bold=False, color=None, italic=False):
    t = {"fontFamily": "Inter", "fontSize": size, "bold": bold, "italic": italic}
    if color:
        t["foregroundColor"] = color
    return t


FMT_FIELDS = "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,padding)"

req = [
    {"unmergeCells": {"range": rng(0, N)}},
    {"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"frozenRowCount": 4, "hideGridlines": True}},
        "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines"}},
    # базовый вид листа; захватываем запас строк ниже данных, чтобы после
    # сокращения таблицы там не оставалось заливки от прошлой версии
    cell(FMT_FIELDS, range=rng(0, N + 40), backgroundColor=WHITE, textFormat=text(),
         verticalAlignment="MIDDLE", wrapStrategy="CLIP",
         padding={"top": 2, "bottom": 2, "left": 8, "right": 8}),
    # и снимаем с этого запаса границы
    {"updateBorders": {
        "range": rng(N, N + 40),
        "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
        "left": {"style": "NONE"}, "right": {"style": "NONE"},
        "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"}}},
]

# ширина колонок
for i, w in enumerate([52, 184, 208, 104, 196, 310, 176, 84, 96]):
    req.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                  "startIndex": i, "endIndex": i + 1},
        "properties": {"pixelSize": w}, "fields": "pixelSize"}})

# шапка документа
req += [
    {"mergeCells": {"range": rng(0, 1), "mergeType": "MERGE_ALL"}},
    cell(FMT_FIELDS, range=rng(0, 1), backgroundColor=WHITE,
         textFormat=text(18, bold=True, color=INK), verticalAlignment="MIDDLE",
         padding={"top": 2, "bottom": 2, "left": 8, "right": 8}),
    {"mergeCells": {"range": rng(1, 2), "mergeType": "MERGE_ALL"}},
    cell(FMT_FIELDS, range=rng(1, 2), backgroundColor=WHITE,
         textFormat=text(10, color=MUTED), verticalAlignment="MIDDLE",
         padding={"top": 2, "bottom": 2, "left": 8, "right": 8}),
    cell(FMT_FIELDS, range=rng(3, 4), backgroundColor=NAVY,
         textFormat=text(10, bold=True, color=WHITE),
         horizontalAlignment="CENTER", verticalAlignment="MIDDLE", wrapStrategy="WRAP",
         padding={"top": 2, "bottom": 2, "left": 8, "right": 8}),
]
for r, h in ((0, 34), (1, 20), (2, 8), (3, 32)):
    req.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": r, "endIndex": r + 1},
        "properties": {"pixelSize": h}, "fields": "pixelSize"}})

# строки-секции и подсветка
for i, k in enumerate(kind):
    if k == "zone":
        req += [
            {"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
            cell(FMT_FIELDS, range=rng(i, i + 1), backgroundColor=BLUE,
                 textFormat=text(11, bold=True, color=WHITE), verticalAlignment="MIDDLE",
                 padding={"top": 2, "bottom": 2, "left": 10, "right": 8}),
            {"updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "ROWS",
                          "startIndex": i, "endIndex": i + 1},
                "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
        ]
    elif k == "block":
        req += [
            {"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
            cell(FMT_FIELDS, range=rng(i, i + 1), backgroundColor=PALE,
                 textFormat=text(10, bold=True, color=INK), verticalAlignment="MIDDLE",
                 padding={"top": 2, "bottom": 2, "left": 20, "right": 8}),
        ]
    elif k == "vac":
        req.append(cell("userEnteredFormat.backgroundColor",
                        range=rng(i, i + 1), backgroundColor=AMBER))
    elif k == "res":
        req += [
            cell("userEnteredFormat(backgroundColor,textFormat)", range=rng(i, i + 1),
                 backgroundColor=GREY, textFormat=text(10, color=MUTED, italic=True)),
        ]

# выравнивание служебных колонок в теле таблицы
body0 = kind.index("zone")
req += [
    cell("userEnteredFormat.horizontalAlignment", range=rng(body0, N, 0, 1),
         horizontalAlignment="CENTER"),
    cell("userEnteredFormat.horizontalAlignment", range=rng(body0, N, 7, 9),
         horizontalAlignment="CENTER"),
    cell("userEnteredFormat.horizontalAlignment", range=rng(body0, N, 3, 4),
         horizontalAlignment="CENTER"),
    # сетка только по телу таблицы
    {"updateBorders": {
        "range": rng(3, N),
        "innerHorizontal": {"style": "SOLID", "color": LINE},
        "innerVertical": {"style": "SOLID", "color": LINE}}},
]

call(token, "POST", f"{SPREADSHEET}:batchUpdate", {"requests": req})
print(f"оформление применено: {len(req)} операций, {N} строк")

# ── сверка: то, что в таблице, должно совпадать с тем, что мы отправляли ──
back = call(token, "GET", f"{SPREADSHEET}/values/{quote(TAB)}").get("values", [])
problems = []
for i, want in enumerate(values):
    got = (back[i] if i < len(back) else []) + [""] * NCOLS
    for j, w in enumerate(want):
        if str(w).strip() != str(got[j]).strip():
            problems.append(f"строка {i + 1}, колонка {j + 1}: "
                            f"ожидалось «{w}», в таблице «{got[j]}»")
assert not problems, "расхождения после записи:\n  " + "\n  ".join(problems[:15])

seated = {r[FIO].strip() for r in allocated if not is_vacancy(r)}
in_sheet = {row[4].strip() for row in back[4:] if len(row) > 8 and row[8].strip() == "работает"}
assert seated == in_sheet, f"потерялись: {seated - in_sheet} | лишние: {in_sheet - seated}"
print(f"сверка пройдена: все {len(seated)} сотрудников на месте")
print(f"мест {len(allocated)} — люди {people}, вакансии {vacs}")
print("исключены из рассадки:", [(r[FIO].strip(), r[DEP].strip()) for r in excluded])
for zone, blocks in PLAN:
    o = sum(len(rs) for _, rs in blocks)
    print(f"  {zone}: {o}/{CAPACITY[zone]}")
