# -*- coding: utf-8 -*-
"""Отрисовка вкладки рассадки: запись значений + оформление + сверка.

Скрипты-сборщики формируют два списка одинаковой длины:
    values — строки по 9 колонок
    kind   — тип каждой строки: title / sub / blank / head / zone / block /
             row (сотрудник) / vac (вакансия) / res (резерв)
и передают их в push(). Всё, что касается Sheets, живёт здесь.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SPREADSHEET = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
NCOLS = 9

NAVY = {"red": 0.114, "green": 0.180, "blue": 0.333}
BLUE = {"red": 0.180, "green": 0.459, "blue": 0.714}
PALE = {"red": 0.867, "green": 0.922, "blue": 0.969}
AMBER = {"red": 1.0, "green": 0.949, "blue": 0.800}
GREY = {"red": 0.953, "green": 0.953, "blue": 0.953}
WHITE = {"red": 1, "green": 1, "blue": 1}
INK = {"red": 0.114, "green": 0.180, "blue": 0.333}
MUTED = {"red": 0.60, "green": 0.62, "blue": 0.66}
AMBER_INK = {"red": 0.478, "green": 0.325, "blue": 0.020}
LINE = {"red": 0.851, "green": 0.867, "blue": 0.886}

HEADERS = ["№", "Офис / зона", "Блок", "Отдел", "ФИО", "Должность",
           "Прямой руководитель", "Формат", "Статус"]
WIDTHS = [50, 180, 244, 100, 200, 350, 178, 80, 92]


def font(size=10, bold=False, italic=False, color=None):
    t = {"fontFamily": "Inter", "fontSize": size, "bold": bold, "italic": italic}
    if color:
        t["foregroundColor"] = color
    return t


FULL = ("userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,"
        "verticalAlignment,wrapStrategy,padding)")
PAD = {"top": 2, "bottom": 2, "left": 8, "right": 8}


def ensure_tab(token, tab):
    tabs = get_tabs(token, SPREADSHEET)
    if tab not in tabs:
        call(token, "POST", f"{SPREADSHEET}:batchUpdate",
             {"requests": [{"addSheet": {"properties": {"title": tab}}}]})
        print(f"создана вкладка «{tab}»")
        tabs = get_tabs(token, SPREADSHEET)
    return tabs[tab]


def push(tab, values, kind, expect_people=None):
    assert len(values) == len(kind), "values и kind разной длины"
    token = access_token(load_credentials())
    sheet_id = ensure_tab(token, tab)

    # Слияния снимаем ДО записи: запись в объединённый диапазон сохраняет
    # только верхнюю левую ячейку, остальные значения теряются молча.
    call(token, "POST", f"{SPREADSHEET}:batchUpdate",
         {"requests": [{"unmergeCells": {"range": {"sheetId": sheet_id}}}]})
    call(token, "POST", f"{SPREADSHEET}/values/{quote(tab)}:clear", {})
    res = call(token, "PUT",
               f"{SPREADSHEET}/values/{quote(tab)}?valueInputOption=RAW",
               {"values": values})
    print("записано ячеек:", res.get("updatedCells"))

    N = len(values)

    def rng(r0, r1, c0=0, c1=NCOLS):
        return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
                "startColumnIndex": c0, "endColumnIndex": c1}

    def fmt(range_, fields, **f):
        return {"repeatCell": {"range": range_, "cell": {"userEnteredFormat": f},
                               "fields": fields}}

    req = [
        {"updateSheetProperties": {
            "properties": {"sheetId": sheet_id,
                           "gridProperties": {"frozenRowCount": 4,
                                              "hideGridlines": True}},
            "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines"}},
        # запас строк ниже данных — чтобы от прошлой, более длинной версии
        # не осталось заливки и рамок
        fmt(rng(0, N + 40), FULL, backgroundColor=WHITE, textFormat=font(),
            verticalAlignment="MIDDLE", wrapStrategy="CLIP", padding=PAD),
        {"updateBorders": {
            "range": rng(N, N + 40),
            "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
            "left": {"style": "NONE"}, "right": {"style": "NONE"},
            "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"}}},
    ]
    for i, w in enumerate(WIDTHS):
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
        elif k == "head":
            req.append(fmt(rng(i, i + 1), FULL, backgroundColor=NAVY,
                           textFormat=font(10, bold=True, color=WHITE),
                           horizontalAlignment="CENTER", verticalAlignment="MIDDLE",
                           wrapStrategy="WRAP", padding=PAD))
        elif k == "zone":
            req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                    fmt(rng(i, i + 1), FULL, backgroundColor=BLUE,
                        textFormat=font(11, bold=True, color=WHITE),
                        verticalAlignment="MIDDLE",
                        padding={"top": 2, "bottom": 2, "left": 10, "right": 8}),
                    {"updateDimensionProperties": {
                        "range": {"sheetId": sheet_id, "dimension": "ROWS",
                                  "startIndex": i, "endIndex": i + 1},
                        "properties": {"pixelSize": 28}, "fields": "pixelSize"}}]
        elif k == "block":
            req += [{"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}},
                    fmt(rng(i, i + 1), FULL, backgroundColor=PALE,
                        textFormat=font(10, bold=True, color=INK),
                        verticalAlignment="MIDDLE",
                        padding={"top": 2, "bottom": 2, "left": 20, "right": 8})]
        elif k in ("row", "vac", "res"):
            bg = AMBER if k == "vac" else (GREY if k == "res" else WHITE)
            req.append(fmt(rng(i, i + 1), "userEnteredFormat.backgroundColor",
                           backgroundColor=bg))
            if k == "res":
                req.append(fmt(rng(i, i + 1), "userEnteredFormat.textFormat",
                               textFormat=font(10, italic=True, color=MUTED)))
            else:
                # служебные колонки приглушаем, ФИО выделяем — взгляд идёт по людям
                req += [
                    fmt(rng(i, i + 1, 1, 3), "userEnteredFormat.textFormat",
                        textFormat=font(9, color=MUTED)),
                    fmt(rng(i, i + 1, 4, 5), "userEnteredFormat.textFormat",
                        textFormat=font(10, bold=(k == "row"), color=INK)),
                    fmt(rng(i, i + 1, 7, 8), "userEnteredFormat.textFormat",
                        textFormat=font(9, color=MUTED)),
                    fmt(rng(i, i + 1, 8, 9), "userEnteredFormat.textFormat",
                        textFormat=font(9, bold=(k == "vac"),
                                        color=AMBER_INK if k == "vac" else MUTED)),
                ]

    body0 = kind.index("zone")
    req += [
        fmt(rng(body0, N, 0, 1), "userEnteredFormat.horizontalAlignment",
            horizontalAlignment="CENTER"),
        fmt(rng(body0, N, 3, 4), "userEnteredFormat.horizontalAlignment",
            horizontalAlignment="CENTER"),
        fmt(rng(body0, N, 7, 9), "userEnteredFormat.horizontalAlignment",
            horizontalAlignment="CENTER"),
        fmt(rng(4, N, 5, 7), "userEnteredFormat.wrapStrategy", wrapStrategy="WRAP"),
        {"updateBorders": {
            "range": rng(3, N),
            "innerHorizontal": {"style": "SOLID", "color": LINE},
            "innerVertical": {"style": "SOLID", "color": LINE}}},
    ]

    call(token, "POST", f"{SPREADSHEET}:batchUpdate", {"requests": req})
    print(f"оформление: {len(req)} операций, {N} строк")

    # ── сверка: в таблице должно оказаться ровно то, что отправляли ──
    back = call(token, "GET", f"{SPREADSHEET}/values/{quote(tab)}").get("values", [])
    problems = []
    for i, want in enumerate(values):
        got = (back[i] if i < len(back) else []) + [""] * NCOLS
        for j, w in enumerate(want):
            if str(w).strip() != str(got[j]).strip():
                problems.append(f"строка {i+1} кол.{j+1}: «{w}» ≠ «{got[j]}»")
    assert not problems, "расхождения после записи:\n  " + "\n  ".join(problems[:15])

    if expect_people is not None:
        in_sheet = {r[4].strip() for r in back[4:]
                    if len(r) > 8 and r[8].strip() == "работает"}
        assert expect_people == in_sheet, (
            f"потерялись: {expect_people - in_sheet} | лишние: {in_sheet - expect_people}")
        print(f"сверка пройдена: все {len(expect_people)} сотрудников на месте")
    return sheet_id
