# -*- coding: utf-8 -*-
"""Вариант рассадки: все московские сотрудники в одном новом офисе.

Отличие от основной вкладки — нет деления на Остоженку и новый офис,
поэтому ёмкость крыльев не ограничивает. Считаем, сколько мест нужно.
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

TAB = "Рассадка — все в новом офисе"
FIO, GRADE, POS, DEP, VAC, FMT, CITY, MGR = 3, 5, 6, 7, 8, 9, 10, 11
EXCLUDED_DEPS = {"MAZE", "ВЭД"}

rows = [l.rstrip("\n").split("\t") for l in open("shtat.tsv", encoding="utf-8")]
data = [r + [""] * (12 - len(r)) for r in rows[1:] if any(c.strip() for c in r)]


def needs_seat(r):
    return r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")


def is_vacancy(r):
    return r[FIO].strip() == "Вакансия" or r[VAC].strip() == "Вакансия"


pool = {}
for r in data:
    if not needs_seat(r):
        continue
    dep = r[DEP].strip()
    if dep in EXCLUDED_DEPS:
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


ZONE = "Новый офис — единая площадка"
ZONE_SHORT = "Новый офис"   # в строках, чтобы колонка не обрезалась

# Порядок блоков: руководство, продуктово-технический контур, затем
# коммерческий, затем поддерживающие функции.
BLOCKS = [
    ("Кабинеты руководства",
     take("АУП", exclude={"Печенев Андрей"})
     + take("Маркетинг", match={"Носенко Вячеслав"})
     + take("Продукт", match={"Головко Илья"})
     + take("Фин", match={"Зеленцов Александр"})),
    # CDO и CTO сидят с командой, как в основном варианте
    ("ИТ — опенспейс",
     take("АУП", match={"Печенев Андрей"})
     + take("ИТ", match={"Шияфетдинов Дамир"})
     + take("ИТ")),
    ("AI", take("AI")),
    ("Продукт — опенспейс", take("Продукт")),
    ("Маркетинг — опенспейс", take("Маркетинг")),
    ("PR и развитие", take("PR")),
    ("Продажи и рефералы", take("Продажи") + take("Рефералы")),
    ("Партнёры и юристы", take("Партнеры") + take("ЮО")),
    # руководитель отдела кадров сидит с главным бухгалтером
    ("Финансовый блок", take("Фин") + take("HR", match={"Смелова Наталья"})),
    ("HR", take("HR")),
    ("Забота и качество", take("Забота") + take("ОКК")),
    ("Ресепшн / АХО", take("АХО")),
]

allocated = [r for _, rs in BLOCKS for r in rs]
everyone = [r for rs in pool.values() for r in rs]
assert len(allocated) == len(set(map(id, allocated))), "дубли мест"
missing = [r for r in everyone if r not in allocated]
assert not missing, f"не рассажены: {[(r[FIO], r[DEP]) for r in missing]}"

people = sum(1 for r in allocated if not is_vacancy(r))
vacs = len(allocated) - people

# резерв — одно место на отдел, в блоке, где у отдела больше всего мест
dept_block = defaultdict(Counter)
for block, rs in BLOCKS:
    for r in rs:
        dept_block[r[DEP].strip()][block] += 1
RESERVE_AT = defaultdict(list)
for dep, cnt in dept_block.items():
    RESERVE_AT[cnt.most_common(1)[0][0]].append(dep)
reserve_total = sum(len(v) for v in RESERVE_AT.values())
total = len(allocated) + reserve_total

values, kind = [], []


def put(row, k):
    values.append(row + [""] * (render.NCOLS - len(row)))
    kind.append(k)


put(["РАССАДКА — ВСЕ В НОВОМ ОФИСЕ"], "title")
put([f"Вариант: вся Москва на одной площадке · требуется {total} мест = "
     f"{people} сотрудников + {vacs} вакансий + {reserve_total} резерв (по одному на отдел) · "
     f"источники: ШТАТКА + вакансии «Штат 21 09 26» · без отделов {', '.join(sorted(EXCLUDED_DEPS))}"], "sub")
put([], "blank")
put(render.HEADERS, "head")

put([f"{ZONE}      сотрудников {people}   вакансий {vacs}   "
     f"резерв {reserve_total}      всего мест {total}"], "zone")

seat = 0
for block, rs in BLOCKS:
    res_deps = sorted(RESERVE_AT[block])
    put([f"{block}  ·  {len(rs)}" + (f"  + резерв {len(res_deps)}" if res_deps else "")],
        "block")
    for r in rs:
        seat += 1
        vac = is_vacancy(r)
        name = r[FIO].strip()
        put([seat, ZONE_SHORT, block, r[DEP].strip(),
             name if name and name != "Вакансия" else "—",
             r[POS].strip(), r[MGR].strip() or "—", r[FMT].strip(),
             "вакансия" if vac else "работает"], "vac" if vac else "row")
    for dep in res_deps:
        seat += 1
        put([seat, ZONE_SHORT, block, dep, "—", f"— резерв отдела {dep} —", "—", "—",
             "резерв"], "res")

render.push(TAB, values, kind,
            expect_people={r[FIO].strip() for r in allocated if not is_vacancy(r)})

print(f"\nвсего мест: {total} (люди {people} + вакансии {vacs} + резерв {reserve_total})")
for block, rs in BLOCKS:
    extra = len(RESERVE_AT[block])
    print(f"  {block:<26} {len(rs):>3}" + (f" + {extra} резерв" if extra else ""))
