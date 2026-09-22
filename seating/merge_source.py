# -*- coding: utf-8 -*-
"""Объединяет два источника в один файл, который читают все сборщики.

По решению заказчика:
  * состав сотрудников и их должности — из вкладки «ШТАТКА»
    файла «Список сотрудников 21 09» (актуальный источник);
  * строки-вакансии — из вкладки «Штат 21 09 26» файла переезда,
    в ШТАТКЕ вакансий нет;
  * сотрудники, которые есть во вкладке переезда и сидят на схеме,
    но отсутствуют в ШТАТКЕ, — сохраняются.

Результат пишется в shtat.tsv в той же 12-колоночной раскладке,
что и прежде, поэтому сборщики менять не нужно.
"""
import csv
import re

SRC_SHTATKA = "shtatka.tsv"        # ФИО, Статус, Должность, Отдел, Формат, Город, Рук.
SRC_PEREEZD = "shtat_pereezd.tsv"  # исходная вкладка переезда, 12 колонок
OUT = "shtat.tsv"

HDR = ["№", "Офис (крыло)", "Кабинет", "ФИО", "Проект", "Грейд", "Должность",
       "Отдел", "Статус", "Формат работы", "Город", "Прямой руководитель"]
FIO, POS, DEP, ST, FMT, CITY, MGR = 3, 6, 7, 8, 9, 10, 11

# ШТАТКА называет отдел иначе — приводим к словарю рассадки
DEPT_ALIAS = {"Отдел контроля качества": "ОКК"}

# Одно лицо, записанное в двух источниках по-разному.
# Имя из ШТАТКИ считаем правильным, вариант из вкладки переезда отбрасываем.
SAME_PERSON = {"Гладкова Алёна": "Гладкова Елена"}


def norm(s):
    return tuple(sorted(re.findall(r"[а-яa-z]+", s.lower().replace("ё", "е"))))


shtatka = list(csv.reader(open(SRC_SHTATKA, encoding="utf-8"), delimiter="\t"))[1:]
pereezd = [l.rstrip("\n").split("\t") for l in open(SRC_PEREEZD, encoding="utf-8")]
pereezd = [r + [""] * (12 - len(r)) for r in pereezd[1:] if any(c.strip() for c in r)]


def is_vac(r):
    return r[FIO].strip() == "Вакансия" or r[ST].strip() == "Вакансия"


old_people = {}
for r in pereezd:
    fio = r[FIO].strip()
    if not fio or fio == "Вакансия" or is_vac(r):
        continue
    old_people[norm(SAME_PERSON.get(fio, fio))] = r
vacancies = [r for r in pereezd if is_vac(r)]

out, seen = [], set()

# 1. люди из ШТАТКИ — источник истины по составу и должностям
for r in shtatka:
    fio = r[0].strip()
    if not fio:
        continue
    k = norm(fio)
    seen.add(k)
    prev = old_people.get(k, [""] * 12)     # крыло и кабинет подтянем из прежней вкладки
    dep = DEPT_ALIAS.get(r[3].strip(), r[3].strip())
    out.append(["", prev[1], prev[2], fio, prev[4], prev[5],
                r[2].strip(), dep, "Действующий",
                r[4].strip(), r[5].strip(), r[6].strip()])

# 2. сотрудники, которых в ШТАТКЕ нет, но они есть у переезда (и на схеме)
kept = []
for k, r in old_people.items():
    if k in seen:
        continue
    kept.append(r[FIO].strip())
    out.append(list(r[:12]))

# 3. вакансии — только из вкладки переезда
for r in vacancies:
    row = list(r[:12])
    row[ST] = "Вакансия"
    out.append(row)

for i, row in enumerate(out, start=1):
    row[0] = str(i)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(HDR)
    w.writerows(out)

people = sum(1 for r in out if r[ST] != "Вакансия")
vacs = len(out) - people


def msk(r):
    return r[CITY].strip() == "Москва" and r[FMT].strip() in ("Офис", "Гибрид")


print(f"строк в объединённом источнике: {len(out)} "
      f"(людей {people}, вакансий {vacs})")
print(f"  из ШТАТКИ: {len(shtatka)}")
print(f"  сохранено из вкладки переезда: {len(kept)} — {', '.join(sorted(kept))}")
print(f"  вакансий из вкладки переезда: {vacs}")
print(f"\nнужно мест в Москве (офис/гибрид): {sum(1 for r in out if msk(r))}")
print(f"  людей: {sum(1 for r in out if msk(r) and r[ST] != 'Вакансия')}")
print(f"  вакансий: {sum(1 for r in out if msk(r) and r[ST] == 'Вакансия')}")
