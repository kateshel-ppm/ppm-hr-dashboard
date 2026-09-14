/**
 * Шаблон слайда отдела для презентации «Трекер ППМ Q3 2026».
 *
 * Отличие от текущего шаблона в презентации: рядом с блоком
 * «2 Результат на 15.09» добавлен блок «2.1 Что было сделано за 3 недели».
 *
 * Запуск:  npm i pptxgenjs && node presentation/build-dept-template-slide.js
 * Результат: presentation/dept-template-slide.pptx (титульный слайд + шаблон отдела)
 *            presentation/dept-template-slide.html (превью в браузере)
 *
 * pptxgenjs пишет zip без сжатия (~100 КБ). Чтобы ужать до ~20 КБ:
 *   python3 presentation/recompress-pptx.py presentation/dept-template-slide.pptx
 */

const path = require('path');
const pptxgen = require('pptxgenjs');

// Палитра дашборда ППМ (traker.html / index.html)
const ACCENT = '3B6FE0';
const INK = '1B2A33';
const MUTED = '9AA6A5';
const CARD = 'F6F8F8';
const HAIR = 'E4E9E9';
const GREEN = '12B76A';
const AMBER = 'F79009';
const RED = 'F04438';

const FONT = 'Arial';

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE'; // 13.33 x 7.5
pres.author = 'HR ППМ';
pres.title = 'Трекер ППМ Q3 2026 — шаблон слайда отдела';

const SLIDE_W = 13.33;
const MARGIN = 0.42;
const GAP = 0.12;

// Шесть блоков: 1, 2, 2.1, 3, 4, 5
const COLS = [
  { n: '1', title: 'Цель квартала', w: 1.75, kind: 'goal' },
  { n: '2', title: 'Результат на 15.09', w: 2.15, kind: 'fact' },
  { n: '2.1', title: 'Что было сделано\nза 3 недели', w: 2.35, kind: 'done' },
  { n: '3', title: 'Что ограничивает цель', w: 1.85, kind: 'list' },
  { n: '4', title: 'Гипотезы и решения', w: 1.95, kind: 'list' },
  { n: '5', title: 'Приоритеты на 2 недели', w: 1.85, kind: 'list' },
];

const TOP = 1.22; // верх колонок
const CARD_TOP = 1.92;
const CARD_H = 4.42;
const PAD = 0.14;

// ── Титульный слайд ─────────────────────────────────────────────────────────
const cover = pres.addSlide();
cover.background = { color: 'FFFFFF' };
cover.addText('Промежуточные результаты', {
  x: MARGIN, y: 2.55, w: 9.5, h: 0.8,
  fontFace: FONT, fontSize: 40, bold: true, color: INK,
  isTextBox: true, margin: 0, valign: 'middle',
});
cover.addText('Q3 2026  ·  38 неделя', {
  x: MARGIN, y: 3.42, w: 9.5, h: 0.45,
  fontFace: FONT, fontSize: 18, color: ACCENT,
  isTextBox: true, margin: 0, valign: 'middle',
});
cover.addText('Шаблон слайда отдела: 1 → 2 → 2.1 → 3 → 4 → 5', {
  x: MARGIN, y: 4.05, w: 9.5, h: 0.35,
  fontFace: FONT, fontSize: 11, color: MUTED,
  isTextBox: true, margin: 0, valign: 'middle',
});

const slide = pres.addSlide();
slide.background = { color: 'FFFFFF' };

// ── Шапка ───────────────────────────────────────────────────────────────────
slide.addText('Х отдел', {
  x: MARGIN, y: 0.34, w: 6, h: 0.46,
  fontFace: FONT, fontSize: 28, bold: true, color: INK,
  isTextBox: true, margin: 0, valign: 'middle',
});
slide.addText('Руководитель отдела  ·  факт: 25.08–15.09.2026  ·  цель — на квартал, до 30.09.2026', {
  x: MARGIN, y: 0.78, w: 9.5, h: 0.3,
  fontFace: FONT, fontSize: 10, color: MUTED,
  isTextBox: true, margin: 0, valign: 'middle',
});
slide.addText('Q3 2026  ·  38 неделя', {
  x: SLIDE_W - MARGIN - 3, y: 0.34, w: 3, h: 0.46,
  fontFace: FONT, fontSize: 11, color: MUTED, align: 'right',
  isTextBox: true, margin: 0, valign: 'middle',
});

// ── Колонки ─────────────────────────────────────────────────────────────────
let x = MARGIN;

for (const col of COLS) {
  const isNew = col.n === '2.1';
  const badgeD = 0.32;

  // номер блока в круге
  slide.addShape(pres.ShapeType.ellipse, {
    x, y: TOP, w: badgeD, h: badgeD,
    fill: { color: isNew ? ACCENT : 'EAF1FE' },
    line: { color: isNew ? ACCENT : 'EAF1FE', width: 0 },
  });
  slide.addText(col.n, {
    x: x - 0.06, y: TOP, w: badgeD + 0.12, h: badgeD,
    fontFace: FONT, fontSize: col.n.length > 1 ? 8 : 11, bold: true,
    color: isNew ? 'FFFFFF' : ACCENT, align: 'center', valign: 'middle',
    isTextBox: true, margin: 0,
  });

  // заголовок блока
  slide.addText(col.title, {
    x: x + badgeD + 0.1, y: TOP - 0.03, w: col.w - badgeD - 0.1, h: 0.62,
    fontFace: FONT, fontSize: 11.5, bold: true, color: INK,
    isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.05,
  });

  // карточка блока
  slide.addShape(pres.ShapeType.roundRect, {
    x, y: CARD_TOP, w: col.w, h: CARD_H,
    rectRadius: 0.06,
    fill: { color: isNew ? 'F4F7FE' : CARD },
    line: { color: isNew ? 'D6E2FB' : HAIR, width: 0.75 },
  });

  const cx = x + PAD;
  const cw = col.w - PAD * 2;
  let cy = CARD_TOP + PAD;

  if (col.kind === 'goal') {
    // 4 метрики: название + целевое значение
    for (let i = 0; i < 4; i++) {
      slide.addText('Метрика', {
        x: cx, y: cy, w: cw, h: 0.2,
        fontFace: FONT, fontSize: 9, color: MUTED, isTextBox: true, margin: 0, valign: 'middle',
      });
      slide.addText('цель Х', {
        x: cx, y: cy + 0.2, w: cw, h: 0.3,
        fontFace: FONT, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0, valign: 'middle',
      });
      cy += 1.0;
    }
  } else if (col.kind === 'fact') {
    // 4 метрики: название + факт + статус
    const statuses = [
      { t: 'по плану', c: GREEN },
      { t: 'риск', c: AMBER },
      { t: 'не в плане', c: RED },
      { t: 'по плану', c: GREEN },
    ];
    for (let i = 0; i < 4; i++) {
      slide.addText('Метрика', {
        x: cx, y: cy, w: cw, h: 0.2,
        fontFace: FONT, fontSize: 9, color: MUTED, isTextBox: true, margin: 0, valign: 'middle',
      });
      slide.addText('значение', {
        x: cx, y: cy + 0.2, w: cw * 0.55, h: 0.3,
        fontFace: FONT, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0, valign: 'middle',
      });
      slide.addText(statuses[i].t, {
        x: cx + cw * 0.55, y: cy + 0.22, w: cw * 0.45, h: 0.26,
        fontFace: FONT, fontSize: 8.5, bold: true, color: statuses[i].c, align: 'right',
        isTextBox: true, margin: 0, valign: 'middle',
      });
      cy += 1.0;
    }
  } else if (col.kind === 'done') {
    // что сделано за 3 недели: задача + пояснение
    slide.addText('25.08 → 15.09', {
      x: cx, y: cy, w: cw, h: 0.22,
      fontFace: FONT, fontSize: 8.5, bold: true, color: ACCENT,
      isTextBox: true, margin: 0, valign: 'middle',
    });
    cy += 0.3;
    for (let i = 0; i < 5; i++) {
      slide.addText('Задача', {
        x: cx, y: cy, w: cw, h: 0.22,
        fontFace: FONT, fontSize: 10.5, bold: true, color: INK, isTextBox: true, margin: 0, valign: 'middle',
      });
      slide.addText('описание / результат', {
        x: cx, y: cy + 0.21, w: cw, h: 0.22,
        fontFace: FONT, fontSize: 9, color: MUTED, isTextBox: true, margin: 0, valign: 'middle',
      });
      cy += 0.76;
    }
  } else {
    // списки: 3 пункта
    const items = [];
    for (let i = 0; i < 3; i++) {
      items.push({
        text: '—',
        options: { bullet: false, breakLine: i < 2, paraSpaceAfter: 26 },
      });
    }
    slide.addText(items, {
      x: cx, y: cy, w: cw, h: CARD_H - PAD * 2,
      fontFace: FONT, fontSize: 10.5, color: INK,
      isTextBox: true, margin: 0, valign: 'top',
    });
  }

  x += col.w + GAP;
}

slide.addNotes(
  'Шаблон слайда отдела. Блок 2.1 «Что было сделано за 3 недели» — перечень завершённых ' +
  'задач за период 25.08–15.09: название задачи + краткий результат (цифра или факт).'
);

const out = path.join(__dirname, 'dept-template-slide.pptx');
pres.writeFile({ fileName: out }).then(() => console.log('OK →', out));

// ── HTML-превью с той же геометрией (1 дюйм = 96 px) ────────────────────────
const PX = 96;
const px = (v) => (v * PX).toFixed(1) + 'px';

function colBody(col) {
  if (col.kind === 'goal') {
    return Array.from({ length: 4 }, () =>
      `<div class="row"><div class="m">Метрика</div><div class="v">цель Х</div></div>`).join('');
  }
  if (col.kind === 'fact') {
    const st = [['по плану', GREEN], ['риск', AMBER], ['не в плане', RED], ['по плану', GREEN]];
    return st.map(([t, c]) =>
      `<div class="row"><div class="m">Метрика</div>` +
      `<div class="vline"><span class="v">значение</span>` +
      `<span class="st" style="color:#${c}">${t}</span></div></div>`).join('');
  }
  if (col.kind === 'done') {
    return `<div class="period">25.08 → 15.09</div>` +
      Array.from({ length: 5 }, () =>
        `<div class="task"><div class="t">Задача</div><div class="d">описание / результат</div></div>`).join('');
  }
  return `<div class="dash">—</div><div class="dash">—</div><div class="dash">—</div>`;
}

let cx = MARGIN;
const colsHtml = COLS.map((col) => {
  const isNew = col.n === '2.1';
  const html = `
    <div class="col" style="left:${px(cx)};width:${px(col.w)}">
      <div class="head">
        <span class="badge${isNew ? ' badge-new' : ''}">${col.n}</span>
        <span class="title">${col.title.replace(/\n/g, '<br>')}</span>
      </div>
      <div class="card${isNew ? ' card-new' : ''}">${colBody(col)}</div>
    </div>`;
  cx += col.w + GAP;
  return html;
}).join('');

const html = `<!doctype html>
<html lang="ru"><meta charset="utf-8">
<title>Шаблон слайда отдела — Трекер ППМ Q3 2026</title>
<style>
  body{margin:0;background:#e9edee;display:flex;justify-content:center;padding:24px;font-family:Arial,Helvetica,sans-serif}
  .slide{position:relative;width:${px(SLIDE_W)};height:${px(7.5)};background:#fff;box-shadow:0 2px 18px rgba(0,0,0,.12)}
  .dept{position:absolute;left:${px(MARGIN)};top:${px(0.34)};font-size:28pt;font-weight:700;color:#${INK};line-height:${px(0.46)}}
  .sub{position:absolute;left:${px(MARGIN)};top:${px(0.78)};font-size:10pt;color:#${MUTED};line-height:${px(0.3)}}
  .wk{position:absolute;right:${px(MARGIN)};top:${px(0.34)};font-size:11pt;color:#${MUTED};line-height:${px(0.46)}}
  .col{position:absolute;top:${px(TOP)}}
  .head{display:flex;gap:${px(0.1)};align-items:flex-start;height:${px(0.62)}}
  .badge{flex:0 0 auto;width:${px(0.32)};height:${px(0.32)};border-radius:50%;background:#EAF1FE;color:#${ACCENT};
         font-size:11pt;font-weight:700;display:flex;align-items:center;justify-content:center}
  .badge-new{background:#${ACCENT};color:#fff;font-size:8pt}
  .title{font-size:11.5pt;font-weight:700;color:#${INK};line-height:1.05}
  .card{position:absolute;top:${px(CARD_TOP - TOP)};left:0;right:0;height:${px(CARD_H)};
        box-sizing:border-box;padding:${px(PAD)};border:1px solid #${HAIR};border-radius:6px;background:#${CARD}}
  .card-new{background:#F4F7FE;border-color:#D6E2FB}
  .row{height:${px(1.0)}}
  .m{font-size:9pt;color:#${MUTED};line-height:${px(0.2)}}
  .v{font-size:14pt;font-weight:700;color:#${INK};line-height:${px(0.3)}}
  .vline{display:flex;align-items:baseline;justify-content:space-between;height:${px(0.3)}}
  .st{font-size:8.5pt;font-weight:700}
  .period{font-size:8.5pt;font-weight:700;color:#${ACCENT};line-height:${px(0.22)};margin-bottom:${px(0.08)}}
  .task{height:${px(0.76)}}
  .task .t{font-size:10.5pt;font-weight:700;color:#${INK};line-height:${px(0.22)}}
  .task .d{font-size:9pt;color:#${MUTED};line-height:${px(0.22)}}
  .dash{font-size:10.5pt;color:#${INK};margin-bottom:${px(0.36)}}
</style>
<div class="slide">
  <div class="dept">Х отдел</div>
  <div class="sub">Руководитель отдела &middot; факт: 25.08–15.09.2026 &middot; цель — на квартал, до 30.09.2026</div>
  <div class="wk">Q3 2026 &middot; 38 неделя</div>
  ${colsHtml}
</div>
</html>`;

const htmlOut = path.join(__dirname, 'dept-template-slide.html');
require('fs').writeFileSync(htmlOut, html);
console.log('OK →', htmlOut);
