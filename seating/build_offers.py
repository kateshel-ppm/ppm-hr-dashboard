# -*- coding: utf-8 -*-
"""Вкладка «Варианты офисов»: все предложения из КП брокеров в одной таблице.

Источники (PDF от заказчика, 22.09.2026; в репозиторий не кладём):
  * OF.RU, подборки от 16.09, 18.09 и 22.09.2026 (Алина Зубкова);
  * Space 1 JET Красная Роза, КП от 10.09.2026;
  * коворкинг «Рябовская мануфактура», Холодильный 3, 3 этаж — 4 опции.
    Опция 4 (85 мест) — это и есть план с кабинетами 345–349, по которому
    построены вкладки «Рассадка — новый офис …».

Цены — как в КП. Где НДС не включён, добавляем 22 % (ставка из КП коворкинга)
в отдельной колонке, чтобы сравнивать одинаково. Для классической аренды
мест по КП нет — оцениваем по 8 м² на место (плотный опенспейс с
переговорными); это оценка, а не обещание арендодателя.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheets_write import access_token, call, get_tabs, load_credentials, quote  # noqa: E402

SID = "1Th3VjPok7vwOGWgipxAUBp0czCAyUTJNmW0xUIPCIOI"
TAB = "Варианты офисов"
NCOLS = 10
VAT = 0.22
M2_PER_SEAT = 8

# сценарии из вкладок рассадки
NEED = [("Вариант 2 — едут ИТ и продукт", 40, "Рассадка — новый офис (без маркетинга)"),
        ("Вариант 1 — едут все, кроме списка", 54, "Рассадка — новый офис (полный переезд)"),
        ("Вся компания в одном офисе", 77, "62 человека + 15 вакансий, Остоженка закрывается")]

# (объект, адрес / метро, класс, площадь м², мест по КП, руб/мес по КП,
#  НДС, готовность, тип договора, комментарий, источник)
SERVICED = [
    ("Коворкинг Рябовская мануфактура, опция 1", "Холодильный пер., 3, 3 эт. / Тульская 3 мин", "B+",
     None, 53, 1_855_000, "включён 22 %", "скидка при договоре до 01.10.2026", "11 мес – 5 лет, депозит 1 мес",
     "готовый офис с мебелью, кухни, переговорные, уборка, интернет — единый платёж", "КП коворкинга"),
    ("Коворкинг Рябовская мануфактура, опция 2", "Холодильный пер., 3, 3 эт. / Тульская 3 мин", "B+",
     None, 67, 2_345_000, "включён 22 %", "скидка при договоре до 01.10.2026", "11 мес – 5 лет, депозит 1 мес",
     "то же", "КП коворкинга"),
    ("Коворкинг Рябовская мануфактура, опция 3", "Холодильный пер., 3, 3 эт. / Тульская 3 мин", "B+",
     None, 71, 2_733_500, "включён 22 %", "скидка при договоре до 01.10.2026", "11 мес – 5 лет, депозит 1 мес",
     "блок офисов, рассадка по нашему ТЗ", "КП коворкинга"),
    ("Коворкинг Рябовская мануфактура, опция 4", "Холодильный пер., 3, 3 эт. / Тульская 3 мин", "B+",
     None, 85, 3_187_500, "включён 22 %", "скидка при договоре до 01.10.2026", "11 мес – 5 лет, депозит 1 мес",
     "ПЛАН 345–349 — по нему построены рассадки «новый офис»", "КП коворкинга"),
    ("Space 1 JET Красная Роза, офисы 115 + 109", "Тимура Фрунзе, 11с13, 3 эт. / Парк Культуры", "B+",
     None, 43, 2_365_000, "не включён", "готово", "по КП", "28 + 15 мест, два офиса рядом; всё включено, парковка 36 000/мес",
     "КП Space 1"),
    ("Space 1 JET Красная Роза, офис 102", "Тимура Фрунзе, 11с13, 3 эт. / Парк Культуры", "B+",
     None, 65, 3_575_000, "не включён", "готово", "по КП", "один большой офис; всё включено", "КП Space 1"),
    ("Space 1 JET Красная Роза, офисы 102 + 109", "Тимура Фрунзе, 11с13, 3 эт. / Парк Культуры", "B+",
     None, 80, 4_400_000, "не включён", "готово", "по КП", "65 + 15 мест; всё включено", "КП Space 1"),
    ("БЦ Газетный 17, 10 эт.", "Газетный пер., 17 / Тверская 7 мин", "A",
     287, 41, 2_217_553, "не включён", "готово", "субаренда, депозит 3 мес", "«41 рабочее место, всё включено»",
     "OF.RU 22.09"),
    ("Особняк Центр оперного пения Вишневской, 3 эт.", "Остоженка, 25с1 / Парк Культуры 6 мин", "A",
     285, 47, 2_726_000, "включён", "готово", "прямая, депозит 2 мес",
     "«47 рабочих мест, всё включено»; ТА ЖЕ УЛИЦА, что текущий офис", "OF.RU 22.09"),
]

CLASSIC = [
    ("БЦ Дельта Плаза, 4 эт.", "2-й Сыромятнический, 1 / Чкаловская 3 мин", "A",
     231, None, 1_503_040, "не включён", "готово", "прямая, депозит 2 мес", "с мебелью; ставка 52 000 + OPEX 12 000", "OF.RU 22.09"),
    ("БЦ Галерея Актёр, 6 эт., 263 м²", "Тверская, 16с1 / Пушкинская 1 мин", "B+",
     263, None, 1_336_917, "не включён", "готово", "прямая, депозит 2 мес", "с мебелью; ставка 50 000 + OPEX", "OF.RU 22.09"),
    ("БЦ Сады Пекина, 2 эт., 407 м²", "Б. Садовая, 5к1 / Маяковская 5 мин", "A",
     407, None, 2_886_000, "включён", "готово", "прямая", "ставка 85 091; из сравнительной таблицы КП", "OF.RU 16.09"),
    ("ОЖК Онегин, 2 эт.", "Малая Полянка, 2 / Полянка 2 мин", "B+",
     432, None, 7_027_200, "включён", "готово", "прямая, депозит 2 мес", "ставка 195 200 — самая дорогая в подборке", "OF.RU 16.09"),
    ("БП Рябовская мануфактура, Гончар, 3 эт., 445 м²", "Холодильный пер., 3 / Тульская 4 мин", "B+",
     445, None, 3_000_000, "включён", "01.02.2027", "прямая, депозит 1 мес", "ставка 80 899", "OF.RU 16.09"),
    ("ЖК Композиторская 17, 6 эт.", "Композиторская, 17 / Смоленская 5 мин", "B+",
     456, None, 4_758_000, "включён", "01.10.2026", "прямая, депозит 2 мес", "ставка 125 211; коммуналка включена", "OF.RU 16.09"),
    ("БП Рябовская мануфактура, стр. 3, 1 эт.", "Холодильный пер., 3к1с3 / Тульская 2 мин", "B+",
     474, None, 2_172_500, "включён", "под освобождение", "прямая, депозит 2 мес", "ставка 55 000; здание 1875 г., сплиты", "OF.RU 16.09"),
    ("БП Рябовская мануфактура, Гончар, 3 эт., 500 м²", "Холодильный пер., 3 / Тульская 4 мин", "B+",
     500, None, 2_745_500, "включён", "01.10.2026", "прямая, депозит 1 мес", "ставка 65 892", "OF.RU 16.09"),
    ("БЦ 1-й Щипковский 5, 3 эт.", "1-й Щипковский пер., 5 / Серпуховская 8 мин", "A",
     520, None, 5_868_200, "включён", "готово", "прямая, депозит 2 мес", "ставка 135 420", "OF.RU 16.09"),
    ("БП Поклонка Плейс, корп. Е, 1 эт.", "Поклонная, 3к4 / Кутузовская 6 мин", "A",
     532, None, 2_848_700, "включён", "01.10.2026", "субаренда, депозит 2 мес", "ставка 64 256", "OF.RU 16.09"),
    ("Особняк Б. Полянка 2с2, мансарда", "Б. Полянка, 2с2 / Полянка 5 мин", "B+",
     556, None, 3_675_555, "включён", "готово", "субаренда, депозит 2 мес", "ставка 79 300 с НДС (база 65 000)", "OF.RU 18.09"),
    ("Особняк Садовническая наб. 9, 3 эт.", "Садовническая наб., 9 / Третьяковская 6 мин", "B+",
     575, None, 5_750_000, "включён", "готово", "прямая, депозит 2 мес", "ставка 120 000; коммуналка включена", "OF.RU 16.09"),
    ("БЦ Галерея Актёр, 6 эт., 593 м²", "Тверская, 16с1 / Пушкинская 1 мин", "B+",
     593, None, 8_344_800, "включён", "готово", "прямая, депозит 3 мес", "ставка 168 866", "OF.RU 16.09"),
    ("БЦ Спейс 1 Балчуг, 3 эт.", "Садовническая, 9А / Новокузнецкая 8 мин", "A",
     716, None, 7_930_000, "включён", "готово", "прямая, депозит 2 мес", "ставка 132 905; коммуналка включена", "OF.RU 16.09"),
    ("БП Орджоникидзе 11с1А, 1 эт.", "Орджоникидзе, 11с1А / Ленинский пр-т 10 мин", "B",
     739, None, 3_079_167, "включён", "09.10.2026", "прямая, депозит 2 мес", "ставка 50 000; кабинетная планировка", "OF.RU 18.09"),
    ("БЦ Премьер Плаза, стр. 4, 2 эт.", "пер. Капранова, 3с4 / Краснопресненская 3 мин", "B+",
     740, None, 3_700_000, "включён", "20.07.2026", "прямая, КРАТКОСРОЧНЫЙ", "ставка 60 000", "OF.RU 18.09"),
    ("БЦ Павелецкая Плаза, 7 эт.", "Павелецкая пл., 2с1 / Павелецкая 1 мин", "A",
     743, None, 8_405_800, "включён", "готово", "прямая, депозит 3 мес", "ставка 135 760", "OF.RU 16.09"),
    ("БП Рябовская мануфактура, стр. 6, 1 эт.", "Холодильный пер., 3к1с6 / Тульская 1 мин", "B+",
     753, None, 3_451_250, "включён", "готово", "прямая, депозит 2 мес", "ставка 55 000; естественная вентиляция, сплиты", "OF.RU 16.09"),
    ("БП Рябовская мануфактура, Гончар, 1 эт., 755 м²", "Холодильный пер., 3 / Тульская 4 мин", "B+",
     755, None, 3_460_417, "включён", "01.10.2026", "прямая, депозит 2 мес", "ставка 55 000", "OF.RU 16.09"),
    ("БЦ Летниковская 5, 3 эт.", "Летниковская, 5 / Павелецкая 3 мин", "B",
     804, None, 2_814_000, "УСН, НДС 5 % вкл.", "30.09.2026", "прямая, депозит 1 мес", "ставка 42 000 — самая низкая в подборке", "OF.RU 18.09"),
    ("БЦ Сады Пекина, 3 эт., 811 м²", "Б. Садовая, 5к1 / Маяковская 5 мин", "A",
     811, None, 5_342_395, "включён", "готово", "прямая, депозит 2 мес", "ставка 79 049; коммуналка включена", "OF.RU 16.09"),
    ("БЦ На Тульской, 3 эт.", "Б. Тульская, 19 / Тульская 1 мин", "B+",
     950, None, 3_780_000, "включён", "готово", "прямая, депозит 2 мес", "ставка 47 747; коммуналка включена", "OF.RU 18.09"),
]

NAVY = {"red": 0.114, "green": 0.180, "blue": 0.333}
BLUE = {"red": 0.180, "green": 0.459, "blue": 0.714}
AMBER = {"red": 1.0, "green": 0.949, "blue": 0.800}
GREEN = {"red": 0.886, "green": 0.945, "blue": 0.898}
GREY = {"red": 0.953, "green": 0.953, "blue": 0.953}
WHITE = {"red": 1, "green": 1, "blue": 1}
INK = NAVY
MUTED = {"red": 0.60, "green": 0.62, "blue": 0.66}
LINE = {"red": 0.851, "green": 0.867, "blue": 0.886}


def with_vat(rent, vat):
    return round(rent * (1 + VAT)) if vat == "не включён" else rent


def fmt_money(x):
    return f"{x:,}".replace(",", " ")


def fits(seats):
    return ", ".join(str(n) for _, n, _ in NEED if seats >= n) or "мало"


values, kind = [], []


def put(row, k):
    values.append([str(c) if c is not None else "" for c in row] + [""] * (NCOLS - len(row)))
    kind.append(k)


put(["ВАРИАНТЫ ОФИСОВ — сводка по КП брокеров (OF.RU 16/18/22.09, Space 1, коворкинг Рябовская мануфактура)"], "title")
put([f"Цены из КП. Где НДС не включён, добавлено {int(VAT*100)} % в колонке «с НДС». Для классической аренды мест по КП нет — "
     f"оценка {M2_PER_SEAT} м² на место (плотный опенспейс с переговорными), это ориентир, не гарантия. "
     f"Колонка «Подходит для» — сколько мест нужно в сценарии: 40 (ИТ + продукт), 54 (все, кроме списка), 77 (вся компания)."], "sub")
put([], "blank")

put(["1. Сколько мест нам нужно"], "sect")
put(["Сценарий", "Мест", "", "Откуда цифра"], "head")
for name, n, src in NEED:
    put([name, n, "", src], "row")
put([], "blank")

put(["2. Готовые офисы «всё включено» — мест по КП"], "sect")
put(["Объект", "Адрес / метро", "Класс", "м²", "Мест", "Руб/мес по КП", "НДС", "Руб/мес с НДС",
     "Руб/место/мес с НДС", "Подходит для · готовность · договор · комментарий"], "head")
for name, addr, cls, area, seats, rent, vat, ready, contract, comment, src in sorted(SERVICED, key=lambda r: r[4]):
    total = with_vat(rent, vat)
    put([name, addr, cls, area or "", seats, fmt_money(rent), vat, fmt_money(total),
         fmt_money(round(total / seats)),
         f"для {fits(seats)} · {ready} · {contract} · {comment} ({src})"],
        "good" if seats >= 40 else "row")
put([], "blank")

put([f"3. Классическая аренда — мест оценка по {M2_PER_SEAT} м²"], "sect")
put(["Объект", "Адрес / метро", "Класс", "м²", "Мест (оценка)", "Руб/мес по КП", "НДС", "Руб/мес с НДС",
     "Руб/место/мес с НДС", "Подходит для · готовность · договор · комментарий"], "head")
for name, addr, cls, area, _, rent, vat, ready, contract, comment, src in CLASSIC:
    seats = area // M2_PER_SEAT
    total = with_vat(rent, vat)
    cheap = total / seats <= 45_000
    put([name, addr, cls, area, seats, fmt_money(rent), vat, fmt_money(total),
         fmt_money(round(total / seats)),
         f"для {fits(seats)} · {ready} · {contract} · {comment} ({src})"],
        "good" if cheap and seats >= 40 else ("amber" if total / seats > 90_000 else "row"))
put([], "blank")

put(["4. Самые дешёвые варианты под каждый сценарий (с НДС)"], "sect")
put(["Сценарий", "Мест", "Готовый офис", "Руб/мес", "", "Классическая аренда", "Руб/мес", "", "", "Что ещё учесть"], "head")
allrows = [(n, s, with_vat(r, v), "serviced") for n, _, _, _, s, r, v, *_ in SERVICED] + \
          [(n, a // M2_PER_SEAT, with_vat(r, v), "classic") for n, _, _, a, _, r, v, *_ in CLASSIC]
for sc, n, _ in NEED:
    best_s = min((x for x in allrows if x[3] == "serviced" and x[1] >= n), key=lambda x: x[2])
    best_c = min((x for x in allrows if x[3] == "classic" and x[1] >= n), key=lambda x: x[2])
    put([sc, n, best_s[0], fmt_money(best_s[2]), "", best_c[0], fmt_money(best_c[2]), "", "",
         "классика: плюс ремонт, мебель, коммуналка и депозит 2–3 мес; готовый офис — единый платёж"], "grand")
put([], "blank")
put(["Чего нет в КП: стоимость аренды текущего офиса на Остоженке (нужна для сравнения «два офиса против одного»), "
     "стоимость отделки и переезда для классической аренды, срок и условия выхода из текущего договора."], "sub")

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
res = call(token, "PUT", f"{SID}/values/{quote(TAB)}?valueInputOption=RAW", {"values": values})
print("записано ячеек:", res.get("updatedCells"))

N = len(values)
meta = call(token, "GET", f"{SID}?fields=sheets(properties(title,gridProperties))")
props = next(x["properties"] for x in meta["sheets"] if x["properties"]["title"] == TAB)
MAXROWS, MAXCOLS = props["gridProperties"]["rowCount"], props["gridProperties"]["columnCount"]
if MAXCOLS < NCOLS:
    call(token, "POST", f"{SID}:batchUpdate", {"requests": [{"appendDimension": {
        "sheetId": sheet_id, "dimension": "COLUMNS", "length": NCOLS - MAXCOLS}}]})
    MAXCOLS = NCOLS


def rng(r0, r1, c0=0, c1=NCOLS):
    return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
            "startColumnIndex": c0, "endColumnIndex": c1}


def fmt(range_, fields, **f):
    return {"repeatCell": {"range": range_, "cell": {"userEnteredFormat": f}, "fields": fields}}


def font(size=10, bold=False, color=None):
    t = {"fontFamily": "Inter", "fontSize": size, "bold": bold}
    if color:
        t["foregroundColor"] = color
    return t


FULL = ("userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,"
        "verticalAlignment,wrapStrategy,padding)")
PAD = {"top": 2, "bottom": 2, "left": 8, "right": 8}
TAIL = min(N + 40, MAXROWS)
NONE = {"style": "NONE"}

req = [
    {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"hideGridlines": True}},
                               "fields": "gridProperties.hideGridlines"}},
    fmt(rng(0, TAIL, 0, MAXCOLS), FULL, backgroundColor=WHITE, textFormat=font(),
        verticalAlignment="MIDDLE", wrapStrategy="WRAP", padding=PAD),
    {"updateBorders": {"range": rng(0, TAIL, 0, MAXCOLS), "top": NONE, "bottom": NONE, "left": NONE,
                       "right": NONE, "innerHorizontal": NONE, "innerVertical": NONE}},
]
for i, w in enumerate([300, 240, 55, 60, 75, 120, 110, 120, 120, 520]):
    req.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
        "properties": {"pixelSize": w}, "fields": "pixelSize"}})

STYLE = {"grand": (GREEN, font(10, bold=True, color=INK)), "good": (GREEN, None),
         "amber": (AMBER, None), "grey": (GREY, None)}
for i, k in enumerate(kind):
    if k in ("title", "sub", "sect"):
        req.append({"mergeCells": {"range": rng(i, i + 1), "mergeType": "MERGE_ALL"}})
    if k == "title":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=WHITE, textFormat=font(16, bold=True, color=INK),
                       verticalAlignment="MIDDLE", padding=PAD))
    elif k == "sub":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=WHITE, textFormat=font(10, color=MUTED),
                       verticalAlignment="MIDDLE", wrapStrategy="WRAP", padding=PAD))
        req.append({"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": 44}, "fields": "pixelSize"}})
    elif k == "sect":
        req += [fmt(rng(i, i + 1), FULL, backgroundColor=BLUE, textFormat=font(11, bold=True, color=WHITE),
                    verticalAlignment="MIDDLE", padding={"top": 2, "bottom": 2, "left": 10, "right": 8}),
                {"updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": i, "endIndex": i + 1},
                    "properties": {"pixelSize": 28}, "fields": "pixelSize"}}]
    elif k == "head":
        req.append(fmt(rng(i, i + 1), FULL, backgroundColor=NAVY, textFormat=font(10, bold=True, color=WHITE),
                       horizontalAlignment="CENTER", verticalAlignment="MIDDLE", wrapStrategy="WRAP", padding=PAD))
    elif k in STYLE:
        bg, f = STYLE[k]
        if f:
            req.append(fmt(rng(i, i + 1), FULL, backgroundColor=bg, textFormat=f,
                           verticalAlignment="MIDDLE", wrapStrategy="WRAP", padding=PAD))
        else:
            req.append(fmt(rng(i, i + 1), "userEnteredFormat.backgroundColor", backgroundColor=bg))
    if k in ("row", "grand", "good", "amber", "grey"):
        req.append(fmt(rng(i, i + 1, 2, 9), "userEnteredFormat.horizontalAlignment", horizontalAlignment="CENTER"))

start = None
for i, k in enumerate(kind + ["blank"]):
    if k in ("head", "row", "grand", "good", "amber", "grey"):
        start = i if start is None else start
    elif start is not None:
        req.append({"updateBorders": {"range": rng(start, i),
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
for r, k in zip(values, kind):
    if k == "grand":
        print("  ", r[0], "|", r[2], r[3], "|", r[5], r[6])
