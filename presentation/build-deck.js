/**
 * Собирает презентацию «Промежуточные результаты Q3 2026, 38 неделя»
 * со сквозной структурой блоков 1–6 на каждом слайде отдела:
 *
 *   1 Цель квартала
 *   2 Результат на 15.09
 *   3 Что сделал и что помогло (драйвер)
 *   4 Что не сделал и узкое горлышко
 *   5 Гипотезы и решения
 *   6 Приоритеты на 2 недели
 *
 * Содержимое отделов перенесено из презентации «Трекер ППМ Q3 2026».
 *
 * Запуск:  npm i pptxgenjs && node presentation/build-deck.js
 *          python3 presentation/recompress-pptx.py presentation/ppm-q3-w38.pptx
 */

const path = require('path');
const pptxgen = require('pptxgenjs');

// ── Палитра дашборда ППМ ────────────────────────────────────────────────────
const ACCENT = '3B6FE0';
const INK = '1B2A33';
const MUTED = '9AA6A5';
const CARD = 'F6F8F8';
const HAIR = 'E4E9E9';
const GREEN = '12B76A';
const AMBER = 'F79009';
const RED = 'F04438';
const FONT = 'Arial';

// ── Сетка ───────────────────────────────────────────────────────────────────
const SLIDE_W = 13.33;
const MARGIN = 0.42;
const GAP = 0.12;
const TOP = 1.22;
const CARD_TOP = 1.92;
const CARD_H = 4.42;
const PAD = 0.14;

const COLS = [
  { n: '1', title: 'Цель квартала', w: 1.70, kind: 'goal' },
  { n: '2', title: 'Результат на 15.09', w: 2.05, kind: 'fact' },
  { n: '3', title: 'Что сделал\nи что помогло (драйвер)', w: 2.35, kind: 'done' },
  { n: '4', title: 'Что не сделал\nи узкое горлышко', w: 2.30, kind: 'blocked' },
  { n: '5', title: 'Гипотезы и решения', w: 1.80, kind: 'hypo' },
  { n: '6', title: 'Приоритеты на 2 недели', w: 1.70, kind: 'prio' },
];
const ACCENTED = ['3', '4'];

/** Цвет статуса по его тексту. */
function statusColor(text) {
  const t = (text || '').toLowerCase();
  if (/опережа|по плану|норма|снят|закрыт/.test(t)) return GREEN;
  if (/отстаём|отстаем|не в плане|провал/.test(t)) return RED;
  if (/риск|на грани|к \d/.test(t)) return AMBER;
  return MUTED;
}

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.author = 'HR ППМ';
pres.title = 'Промежуточные результаты Q3 2026 — 38 неделя';

// ── Титульный слайд ─────────────────────────────────────────────────────────
function coverSlide() {
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  s.addText('Промежуточные результаты', {
    x: MARGIN, y: 2.55, w: 10, h: 0.8,
    fontFace: FONT, fontSize: 40, bold: true, color: INK,
    isTextBox: true, margin: 0, valign: 'middle',
  });
  s.addText('Q3 2026  ·  38 неделя', {
    x: MARGIN, y: 3.42, w: 10, h: 0.45,
    fontFace: FONT, fontSize: 18, color: ACCENT,
    isTextBox: true, margin: 0, valign: 'middle',
  });
  s.addText('Структура слайда отдела: 1 цель · 2 результат · 3 что сделал и драйвер · ' +
            '4 что не сделал и узкое горлышко · 5 гипотезы · 6 приоритеты', {
    x: MARGIN, y: 4.05, w: 11.5, h: 0.35,
    fontFace: FONT, fontSize: 11, color: MUTED,
    isTextBox: true, margin: 0, valign: 'middle',
  });
}

// ── Слайд отдела ────────────────────────────────────────────────────────────
function deptSlide(cfg) {
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };

  s.addText(cfg.dept, {
    x: MARGIN, y: 0.34, w: 8, h: 0.46,
    fontFace: FONT, fontSize: 26, bold: true, color: INK,
    isTextBox: true, margin: 0, valign: 'middle',
  });
  s.addText(cfg.sub, {
    x: MARGIN, y: 0.78, w: 10.5, h: 0.3,
    fontFace: FONT, fontSize: 10, color: MUTED,
    isTextBox: true, margin: 0, valign: 'middle',
  });
  s.addText('Q3 2026  ·  38 неделя', {
    x: SLIDE_W - MARGIN - 2.6, y: 0.34, w: 2.6, h: 0.46,
    fontFace: FONT, fontSize: 11, color: MUTED, align: 'right',
    isTextBox: true, margin: 0, valign: 'middle',
  });

  let x = MARGIN;
  for (const col of COLS) {
    const hot = ACCENTED.indexOf(col.n) !== -1;
    const badgeD = 0.32;

    s.addShape(pres.ShapeType.ellipse, {
      x, y: TOP, w: badgeD, h: badgeD,
      fill: { color: hot ? ACCENT : 'EAF1FE' },
      line: { color: hot ? ACCENT : 'EAF1FE', width: 0 },
    });
    s.addText(col.n, {
      x: x - 0.06, y: TOP, w: badgeD + 0.12, h: badgeD,
      fontFace: FONT, fontSize: 11, bold: true,
      color: hot ? 'FFFFFF' : ACCENT, align: 'center', valign: 'middle',
      isTextBox: true, margin: 0,
    });
    s.addText(col.title, {
      x: x + badgeD + 0.1, y: TOP - 0.03, w: col.w - badgeD - 0.1, h: 0.62,
      fontFace: FONT, fontSize: 11.5, bold: true, color: INK,
      isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.05,
    });
    s.addShape(pres.ShapeType.roundRect, {
      x, y: CARD_TOP, w: col.w, h: CARD_H,
      rectRadius: 0.06,
      fill: { color: hot ? 'F4F7FE' : CARD },
      line: { color: hot ? 'D6E2FB' : HAIR, width: 0.75 },
    });

    fillCard(s, col, x, cfg);
    x += col.w + GAP;
  }

  if (cfg.notes) s.addNotes(cfg.notes);
}

function fillCard(s, col, x, cfg) {
  const cx = x + PAD;
  const cw = col.w - PAD * 2;
  const top = CARD_TOP + PAD;
  const inner = CARD_H - PAD * 2;

  if (col.kind === 'goal' || col.kind === 'fact') {
    const rows = cfg.metrics;
    const pitch = Math.min(1.0, inner / rows.length);
    rows.forEach((m, i) => {
      const y = top + i * pitch;
      // Название, значение и статус — тремя строками на всю ширину колонки:
      // в две колонки длинные подписи вроде «Карты без перевыпуска» переносятся.
      const isGoal = col.kind === 'goal';
      s.addText(m.name, {
        x: cx, y, w: cw, h: 0.2,
        fontFace: FONT, fontSize: 8.5, color: MUTED,
        isTextBox: true, margin: 0, valign: 'middle',
      });
      s.addText(isGoal ? m.goal : m.fact, {
        x: cx, y: y + 0.19, w: cw, h: 0.28,
        fontFace: FONT, fontSize: 12, bold: true, color: INK,
        isTextBox: true, margin: 0, valign: 'middle',
      });
      if (!isGoal && m.status) {
        s.addText(m.status, {
          x: cx, y: y + 0.45, w: cw, h: 0.2,
          fontFace: FONT, fontSize: 8, bold: true, color: statusColor(m.status),
          isTextBox: true, margin: 0, valign: 'middle',
        });
      }
    });
    return;
  }

  const map = { done: cfg.done, blocked: cfg.blocked, hypo: cfg.hypotheses, prio: cfg.priorities };
  const items = map[col.kind] || [];
  const pair = col.kind === 'done' || col.kind === 'blocked';

  if (pair) {
    const label = col.kind === 'done' ? 'факт: 25.08 → 15.09' : 'ключевая сложность';
    s.addText(label, {
      x: cx, y: top, w: cw, h: 0.22,
      fontFace: FONT, fontSize: 8, bold: true,
      color: col.kind === 'done' ? ACCENT : AMBER,
      isTextBox: true, margin: 0, valign: 'middle',
    });
    const body = top + 0.3;
    const pitch = Math.min(0.95, (inner - 0.3) / Math.max(items.length, 1));
    items.forEach((it, i) => {
      const y = body + i * pitch;
      s.addText(it.t, {
        x: cx, y, w: cw, h: 0.42,
        fontFace: FONT, fontSize: 9.5, bold: true, color: INK,
        isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.02,
      });
      s.addText(it.d, {
        x: cx, y: y + 0.44, w: cw, h: pitch - 0.44,
        fontFace: FONT, fontSize: 8.5, color: MUTED,
        isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.02,
      });
    });
    return;
  }

  const runs = items.map((t, i) => ({
    text: t,
    options: { bullet: false, breakLine: i < items.length - 1, paraSpaceAfter: 12 },
  }));
  s.addText(runs.length ? runs : [{ text: '—' }], {
    x: cx, y: top, w: cw, h: inner,
    fontFace: FONT, fontSize: 9.5, color: INK,
    isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.05,
  });
}

// ── Данные отделов (перенесены из «Трекер ППМ Q3 2026») ─────────────────────

const TODO = [
  { t: 'Заполнить: задача — результат', d: 'драйвер: что помогло её сделать' },
  { t: 'Заполнить: задача — результат', d: 'драйвер: что помогло её сделать' },
  { t: 'Заполнить: задача — результат', d: 'драйвер: что помогло её сделать' },
];

const COMMERCIAL = {
  dept: 'Коммерческий блок',
  sub: 'факт: 25.08–15.09.2026  ·  цель — на квартал, до 30.09.2026',
  metrics: [
    { name: 'Чистая прибыль', goal: '411 млн ₽', fact: '368 млн ₽', status: '90%, опережаем' },
    { name: 'Contribution', goal: '580 млн ₽', fact: '528 млн ₽', status: '91%, опережаем' },
    { name: 'GP', goal: '861 млн ₽', fact: '769 млн ₽', status: '89%, опережаем' },
    { name: 'Новые клиенты', goal: '127 тыс', fact: '90,5 тыс', status: '71%, отстаём' },
    { name: 'Карты без перевыпуска', goal: '126 тыс', fact: '98,7 тыс', status: '78%, отстаём' },
  ],
  done: TODO,
  blocked: [
    { t: 'Привлечение просело', d: 'приток новых 34,6 тыс к концу сентября против плана 44,5' },
    { t: 'Воронка', d: 'визит→рег 2,1% при цели 2,3%, провал на переходе к выпуску карты' },
    { t: 'Деньги держат премиум и переезд', d: 'а не новые клиенты' },
  ],
  hypotheses: [
    'Дофинансирование: +52 млн бюджета дают +26 млн прибыли (0,5 ₽ на рубль)',
    'Рассылка по 45 тыс регистраций без карты — до 1 300 карт',
    'Партнёрка и рефка конвертят 54% и 78% — растить их долю',
  ],
  priorities: [
    'Открутить остаток бюджета: 61 млн за 17 дней',
    'Починить переход со страницы карт на выпуск',
    'Закрыть август по koko и перекалибровать переезд на сентябрьский PL',
  ],
  notes: 'Блок 3 не заполнен: в исходной презентации списка сделанного за 3 недели не было.',
};

const LEGAL = {
  dept: 'Юридический департамент',
  sub: 'Руководитель юрдепартамента  ·  факт: 25.08–15.09.2026  ·  цель — на квартал, до 30.09.2026',
  metrics: [
    { name: 'Аудит группы компаний', goal: 'Светофор', fact: 'Светофор', status: 'По плану' },
    { name: 'Топ-риск по матрице', goal: 'Снять 1', fact: 'Снят', status: 'По плану' },
    { name: 'Риск ПДн', goal: 'Закрыть', fact: 'К 30.09', status: 'Риск' },
    { name: 'Второй риск', goal: 'Закрыть', fact: 'Агенты Claude', status: 'Риск' },
    { name: 'Документооборот', goal: '10 шаблонов', fact: 'SLA 2 р.д.', status: 'По плану' },
  ],
  done: [
    { t: 'Матрица рисков по группе', d: 'светофор, топ-риск № 1 снят' },
    { t: 'Документооборот', d: 'Яндекс Трекер, 10 шаблонов, SLA 2 р.д.' },
    { t: 'Прецедент Банк 131', d: 'договор поручения в двух редакциях' },
    { t: 'НСПК', d: 'реестр v19, проект Соглашения вместо суда' },
    { t: '28 договоров с правками', d: 'NDA Сбербанк, ТБанк, МТС, Т2' },
  ],
  blocked: [
    { t: 'Второй риск', d: 'закроется полностью только когда Банк заберёт услугу под ключ' },
    { t: 'Риск ПДн', d: 'ждём картину фактических потоков данных от продукта и разработки' },
    { t: '28 договоров за 10 рабочих дней', d: 'при одном юристе в отделе' },
  ],
  hypotheses: [
    'Агенты в Claude запускаются при каждом согласовании договора',
    'KYC/AML закрываем партнёрством с Банком 131, а не своим штатом',
    'Одна дверь для договоров: Яндекс Трекер, 10 шаблонов, SLA 2 р.д.',
  ],
  priorities: [
    '25.09 — КТ-3 прецедента: договор Банка 131 вычитан, миграция описана',
    '30.09 — ПДн-комплект, аудит рисков, AML, KPI-сверка № 1',
    '01.10 — все договоры идут через одну дверь',
  ],
};

const IT = {
  dept: 'IT отдел',
  sub: 'факт: 25.08–15.09.2026  ·  цель — на квартал, до 30.09.2026',
  metrics: [
    { name: 'SLO', goal: '99,8%', fact: '99,81%', status: 'риск' },
    { name: 'Sprint Predictability', goal: '0,85', fact: 'не подсчитать', status: 'не подсчитать' },
    { name: 'Lead Time for Changes', goal: '2 недели', fact: '4,73 дн', status: 'норма' },
    { name: 'Change Failure Rate', goal: '< 30%', fact: '20%', status: 'норма' },
  ],
  done: TODO,
  blocked: [
    { t: 'Яндекс Трекер', d: 'ограничивает работу с задачами' },
    { t: 'SLO', d: 'упирается в переезд на Яндекс Клауд' },
    { t: 'Тестировщики', d: 'найм не закрыт' },
    { t: 'Sprint Predictability не считается', d: '77–100% задач добавлено после старта спринта' },
  ],
  hypotheses: [
    'Sprint Predictability — вопрос планирования',
    'JIRA решит больше вопросов и не даст манипулировать метрикой',
    'Чёткое планирование на месяц',
  ],
  priorities: [
    'Переезд на Яндекс Клауд — постепенно',
    'Провайдер ZVX',
    'Планы продуктового отдела не известны — синхронизироваться',
  ],
  notes: 'Блок 3 не заполнен: в исходной презентации списка сделанного за 3 недели не было. ' +
         'Блоки 4–6 собраны из исходного слайда, распределение по колонкам стоит перепроверить.',
};

const TEMPLATE = {
  dept: 'Х отдел',
  sub: 'Руководитель отдела  ·  факт: 25.08–15.09.2026  ·  цель — на квартал, до 30.09.2026',
  metrics: [
    { name: 'Метрика', goal: 'цель Х', fact: 'значение', status: 'по плану' },
    { name: 'Метрика', goal: 'цель Х', fact: 'значение', status: 'риск' },
    { name: 'Метрика', goal: 'цель Х', fact: 'значение', status: 'не в плане' },
    { name: 'Метрика', goal: 'цель Х', fact: 'значение', status: 'по плану' },
  ],
  done: [
    { t: 'Задача — результат', d: 'драйвер: что помогло' },
    { t: 'Задача — результат', d: 'драйвер: что помогло' },
    { t: 'Задача — результат', d: 'драйвер: что помогло' },
    { t: 'Задача — результат', d: 'драйвер: что помогло' },
  ],
  blocked: [
    { t: 'Задача — почему не сделана', d: 'узкое горлышко: что мешает' },
    { t: 'Задача — почему не сделана', d: 'узкое горлышко: что мешает' },
    { t: 'Задача — почему не сделана', d: 'узкое горлышко: что мешает' },
  ],
  hypotheses: ['—', '—', '—'],
  priorities: ['—', '—', '—'],
  notes: 'Пустой шаблон отдела: дублируйте этот слайд под каждый отдел.',
};

// ── Сборка ──────────────────────────────────────────────────────────────────
coverSlide();
[COMMERCIAL, LEGAL, IT, TEMPLATE].forEach(deptSlide);

const out = path.join(__dirname, 'ppm-q3-w38.pptx');
pres.writeFile({ fileName: out }).then(() => console.log('OK →', out));

// ── HTML-превью всех слайдов с той же геометрией (1 дюйм = 96 px) ───────────
const PX = 96;
const px = (v) => (v * PX).toFixed(1) + 'px';

function cardHtml(col, cfg) {
  const inner = CARD_H - PAD * 2;

  if (col.kind === 'goal' || col.kind === 'fact') {
    const pitch = Math.min(1.0, inner / cfg.metrics.length);
    return cfg.metrics.map((m, i) => {
      const y = i * pitch;
      const val = col.kind === 'goal' ? m.goal : m.fact;
      const st = col.kind === 'fact' && m.status
        ? `<div class="st" style="color:#${statusColor(m.status)}">${m.status}</div>` : '';
      return `<div class="row" style="top:${px(y)}">
        <div class="m">${m.name}</div>
        <div class="v">${val}</div>${st}</div>`;
    }).join('');
  }

  const map = { done: cfg.done, blocked: cfg.blocked, hypo: cfg.hypotheses, prio: cfg.priorities };
  const items = map[col.kind] || [];

  if (col.kind === 'done' || col.kind === 'blocked') {
    const done = col.kind === 'done';
    const pitch = Math.min(0.95, (inner - 0.3) / Math.max(items.length, 1));
    const head = `<div class="period${done ? '' : ' warn'}">${done ? 'факт: 25.08 → 15.09' : 'ключевая сложность'}</div>`;
    return head + items.map((it, i) => `
      <div class="task" style="top:${px(0.3 + i * pitch)}">
        <div class="t" style="height:${px(0.42)}">${it.t}</div>
        <div class="d">${it.d}</div></div>`).join('');
  }

  return `<div class="list">` + (items.length ? items : ['—'])
    .map((t) => `<p>${t}</p>`).join('') + `</div>`;
}

function slideHtml(cfg) {
  let cx = MARGIN;
  const cols = COLS.map((col) => {
    const hot = ACCENTED.indexOf(col.n) !== -1;
    const html = `
      <div class="col" style="left:${px(cx)};width:${px(col.w)}">
        <div class="head">
          <span class="badge${hot ? ' hot' : ''}">${col.n}</span>
          <span class="title">${col.title.replace(/\n/g, '<br>')}</span>
        </div>
        <div class="card${hot ? ' hot' : ''}">${cardHtml(col, cfg)}</div>
      </div>`;
    cx += col.w + GAP;
    return html;
  }).join('');

  return `<div class="slide">
    <div class="dept">${cfg.dept}</div>
    <div class="sub">${cfg.sub}</div>
    <div class="wk">Q3 2026 &middot; 38 неделя</div>
    ${cols}
  </div>`;
}

const previewHtml = `<!doctype html>
<html lang="ru"><meta charset="utf-8">
<title>Промежуточные результаты Q3 2026 — 38 неделя</title>
<style>
  body{margin:0;background:#e9edee;display:flex;flex-direction:column;align-items:center;gap:24px;
       padding:24px;font-family:Arial,Helvetica,sans-serif}
  .slide{position:relative;width:${px(SLIDE_W)};height:${px(7.5)};background:#fff;box-shadow:0 2px 18px rgba(0,0,0,.12)}
  .dept{position:absolute;left:${px(MARGIN)};top:${px(0.34)};font-size:26pt;font-weight:700;color:#${INK};line-height:${px(0.46)}}
  .sub{position:absolute;left:${px(MARGIN)};top:${px(0.78)};font-size:10pt;color:#${MUTED};line-height:${px(0.3)}}
  .wk{position:absolute;right:${px(MARGIN)};top:${px(0.34)};font-size:11pt;color:#${MUTED};line-height:${px(0.46)}}
  .col{position:absolute;top:${px(TOP)}}
  .head{display:flex;gap:${px(0.1)};align-items:flex-start;height:${px(0.62)}}
  .badge{flex:0 0 auto;width:${px(0.32)};height:${px(0.32)};border-radius:50%;background:#EAF1FE;color:#${ACCENT};
         font-size:11pt;font-weight:700;display:flex;align-items:center;justify-content:center}
  .badge.hot{background:#${ACCENT};color:#fff}
  .title{font-size:11.5pt;font-weight:700;color:#${INK};line-height:1.05}
  .card{position:absolute;top:${px(CARD_TOP - TOP)};left:0;right:0;height:${px(CARD_H)};
        box-sizing:border-box;padding:${px(PAD)};border:1px solid #${HAIR};border-radius:6px;background:#${CARD}}
  .card.hot{background:#F4F7FE;border-color:#D6E2FB}
  .row,.task{position:absolute;left:${px(PAD)};right:${px(PAD)}}
  .m{font-size:8.5pt;color:#${MUTED};line-height:${px(0.19)}}
  .v{font-size:12pt;font-weight:700;color:#${INK};line-height:${px(0.28)}}
  .st{font-size:8pt;font-weight:700;line-height:${px(0.2)}}
  .period{font-size:8pt;font-weight:700;color:#${ACCENT};line-height:${px(0.22)}}
  .period.warn{color:#${AMBER}}
  .task .t{font-size:9.5pt;font-weight:700;color:#${INK};line-height:1.02;overflow:hidden}
  .task .d{font-size:8.5pt;color:#${MUTED};line-height:1.02}
  .list p{margin:0 0 ${px(0.12)};font-size:9.5pt;color:#${INK};line-height:1.05}
</style>
${[COMMERCIAL, LEGAL, IT, TEMPLATE].map(slideHtml).join('\n')}
</html>`;

const htmlOut = path.join(__dirname, 'ppm-q3-w38.html');
require('fs').writeFileSync(htmlOut, previewHtml);
console.log('OK →', htmlOut);
