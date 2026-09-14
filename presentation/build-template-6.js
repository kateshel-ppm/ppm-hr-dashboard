/**
 * Новый шаблон слайда отдела — шесть блоков, сетка 3×2,
 * в оформлении карточек из презентации «Трекер ППМ Q3 2026»:
 *
 *   1 Цель квартала
 *   2 Результаты на 15.09 и главный драйвер
 *   3 Что сделано за 3 недели
 *   4 Что не сделано, что ограничивает цель и где узкое горлышко
 *   5 Гипотезы и решения
 *   6 Приоритеты на 2 недели
 *
 * Запуск:  npm i pptxgenjs && node presentation/build-template-6.js
 *          python3 presentation/recompress-pptx.py presentation/dept-template-6.pptx
 *
 * Геометрия продублирована в presentation/add-template-slide.gs — при правках
 * сетки меняйте оба файла.
 */

const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');

// ── Палитра карточек (снята со слайда-шаблона презентации) ──────────────────
const INK = '2B3A55';       // тёмно-синий, заголовки
const MUTED = '6B7785';     // подписи
const LINE = 'FFFFFF';

const BLOCKS = [
  { n: '1', title: 'Цель квартала',
    bg: 'EDF1FB', key: '2B4C8C', kind: 'goal' },
  { n: '2', title: 'Результаты на 15.09 и главный драйвер',
    bg: 'EAF2EC', key: '3E7D5A', kind: 'fact' },
  { n: '3', title: 'Что сделано за 3 недели',
    bg: 'E6F0F2', key: '2F7382', kind: 'done' },
  { n: '4', title: 'Что не сделано, что ограничивает цель и где узкое горлышко',
    bg: 'FBEDEB', key: 'C0554A', kind: 'list' },
  { n: '5', title: 'Гипотезы и решения',
    bg: 'EDEBF7', key: '5B4E9E', kind: 'list' },
  { n: '6', title: 'Приоритеты на 2 недели',
    bg: 'FBF3E4', key: 'C08420', kind: 'list' },
];

// ── Сетка, дюймы (13.33 × 7.5) ──────────────────────────────────────────────
const SLIDE_W = 13.33, SLIDE_H = 7.5;
const MARGIN = 0.5;
const GAP = 0.28;
const GRID_TOP = 1.25;
const COL_W = (SLIDE_W - MARGIN * 2 - GAP * 2) / 3;
// верхний ряд выше: там метрики и «главный драйвер», нижний — только списки
const ROW1_H = 2.95;
const ROW2_H = SLIDE_H - GRID_TOP - MARGIN - GAP - ROW1_H;
const PAD = 0.25;
const BADGE = 0.3;
const HEAD_H = 0.52;   // высота шапки карточки (кружок + заголовок)
const PITCH = 0.30;    // шаг строки метрики — общий для блоков 1 и 2, чтобы строки совпадали
const rowH = (i) => (i < 3 ? ROW1_H : ROW2_H);
const rowY = (i) => (i < 3 ? GRID_TOP : GRID_TOP + ROW1_H + GAP);

const SERIF = 'Georgia';
const SANS = 'Arial';

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.author = 'HR ППМ';
pres.title = 'Шаблон слайда отдела — 6 блоков';

const slide = pres.addSlide();
slide.background = { color: 'FFFFFF' };

slide.addText('Х отдел', {
  x: MARGIN, y: 0.38, w: 7, h: 0.55,
  fontFace: SERIF, fontSize: 26, bold: true, color: INK,
  isTextBox: true, margin: 0, valign: 'middle',
});
slide.addText('Руководитель отдела  ·  факт: 25.08–15.09.2026  ·  цель — на квартал, до 30.09.2026', {
  x: SLIDE_W - MARGIN - 6, y: 0.45, w: 6, h: 0.4,
  fontFace: SANS, fontSize: 9, color: MUTED, align: 'right',
  isTextBox: true, margin: 0, valign: 'middle',
});

BLOCKS.forEach((b, i) => {
  const col = i % 3;
  const x = MARGIN + col * (COL_W + GAP);
  const y = rowY(i);
  const h = rowH(i);

  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w: COL_W, h,
    rectRadius: 0.14,
    fill: { color: b.bg },
    line: { color: b.bg, width: 0 },
  });
  slide.addShape(pres.ShapeType.ellipse, {
    x: x + PAD, y: y + PAD, w: BADGE, h: BADGE,
    fill: { color: b.key }, line: { color: b.key, width: 0 },
  });
  slide.addText(b.n, {
    x: x + PAD - 0.06, y: y + PAD, w: BADGE + 0.12, h: BADGE,
    fontFace: SANS, fontSize: 11, bold: true, color: LINE,
    align: 'center', valign: 'middle', isTextBox: true, margin: 0,
  });
  slide.addText(b.title, {
    x: x + PAD + BADGE + 0.12, y: y + PAD - 0.04, w: COL_W - PAD * 2 - BADGE - 0.12, h: HEAD_H,
    fontFace: SANS, fontSize: 11, bold: true, color: INK,
    isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.05,
  });

  fillBlock(b, x, y, h);
});

function fillBlock(b, x, y, h) {
  const cx = x + PAD;
  const cw = COL_W - PAD * 2;
  const top = y + PAD + HEAD_H + 0.12;
  const inner = h - PAD * 2 - HEAD_H - 0.12;

  if (b.kind === 'goal' || b.kind === 'fact') {
    const isGoal = b.kind === 'goal';
    const rows = 4;
    const pitch = PITCH;   // одинаковый в блоках 1 и 2 — строки стоят на одной высоте

    for (let i = 0; i < rows; i++) {
      const ry = top + i * pitch;
      slide.addText('Метрика', {
        x: cx, y: ry, w: cw * (isGoal ? 0.52 : 0.42), h: pitch,
        fontFace: SANS, fontSize: 9, color: MUTED,
        isTextBox: true, margin: 0, valign: 'middle',
      });
      slide.addText('значение', {
        x: cx + cw * (isGoal ? 0.52 : 0.42), y: ry, w: cw * (isGoal ? 0.48 : 0.3), h: pitch,
        fontFace: SANS, fontSize: 9.5, bold: true, color: b.key,
        align: isGoal ? 'right' : 'left', isTextBox: true, margin: 0, valign: 'middle',
      });
      if (!isGoal) {
        slide.addText('статус', {
          x: cx + cw * 0.72, y: ry, w: cw * 0.28, h: pitch,
          fontFace: SANS, fontSize: 9.5, bold: true, color: INK,
          align: 'right', isTextBox: true, margin: 0, valign: 'middle',
        });
      }
    }

    if (!isGoal) {
      const dy = y + h - PAD - 0.56;
      slide.addText('ГЛАВНЫЙ ДРАЙВЕР', {
        x: cx, y: dy, w: cw, h: 0.2,
        fontFace: SANS, fontSize: 7.5, bold: true, color: b.key, charSpacing: 1,
        isTextBox: true, margin: 0, valign: 'middle',
      });
      slide.addText('что именно вытянуло результат', {
        x: cx, y: dy + 0.2, w: cw, h: 0.34,
        fontFace: SANS, fontSize: 9.5, color: INK,
        isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.05,
      });
    }
    return;
  }

  if (b.kind === 'done') {
    const rows = 4;
    const pitch = Math.min(0.44, inner / rows);
    for (let i = 0; i < rows; i++) {
      slide.addText('Задача — результат', {
        x: cx, y: top + i * pitch, w: cw, h: pitch,
        fontFace: SANS, fontSize: 9.5, color: INK, bullet: { characterCode: '2022' },
        isTextBox: true, margin: 0, valign: 'top', lineSpacingMultiple: 1.05,
      });
    }
    return;
  }

  const items = [];
  for (let i = 0; i < 3; i++) {
    items.push({ text: ' ', options: { bullet: { characterCode: '2022' }, breakLine: i < 2, paraSpaceAfter: 16 } });
  }
  slide.addText(items, {
    x: cx, y: top, w: cw, h: inner,
    fontFace: SANS, fontSize: 9.5, color: INK,
    isTextBox: true, margin: 0, valign: 'top',
  });
}

slide.addNotes(
  'Шаблон слайда отдела, шесть блоков. 2 — результат и главный драйвер: что именно вытянуло цифру. ' +
  '3 — что сделано за три недели. 4 — что не сделано, что ограничивает цель и где узкое горлышко.'
);

const out = path.join(__dirname, 'dept-template-6.pptx');
pres.writeFile({ fileName: out }).then(() => console.log('OK →', out));

// ── HTML-превью с той же геометрией ─────────────────────────────────────────
const PX = 96;
const px = (v) => (v * PX).toFixed(1) + 'px';

function bodyHtml(b) {
  if (b.kind === 'goal' || b.kind === 'fact') {
    const isGoal = b.kind === 'goal';
    const rows = Array.from({ length: 4 }, () => isGoal
      ? `<div class="r"><span class="mn">Метрика</span><span class="vl" style="color:#${b.key}">значение</span></div>`
      : `<div class="r fact"><span class="mn">Метрика</span>
           <span class="vl" style="color:#${b.key}">значение</span>
           <span class="stt">статус</span></div>`).join('');
    const driver = isGoal ? '' : `
      <div class="driver">
        <div class="dl" style="color:#${b.key}">ГЛАВНЫЙ ДРАЙВЕР</div>
        <div class="dt">что именно вытянуло результат</div>
      </div>`;
    return rows + driver;
  }
  if (b.kind === 'done') {
    return Array.from({ length: 4 }, () => `<div class="li">Задача — результат</div>`).join('');
  }
  return Array.from({ length: 3 }, () => `<div class="li empty">&nbsp;</div>`).join('');
}

const cards = BLOCKS.map((b, i) => {
  const col = i % 3;
  const x = MARGIN + col * (COL_W + GAP);
  const y = rowY(i);
  const h = rowH(i);
  return `<div class="card" style="left:${px(x)};top:${px(y)};width:${px(COL_W)};height:${px(h)};background:#${b.bg}">
      <div class="head">
        <span class="badge" style="background:#${b.key}">${b.n}</span>
        <span class="ct">${b.title}</span>
      </div>
      <div class="body" style="height:${px(h - PAD * 2 - HEAD_H - 0.12)}">${bodyHtml(b)}</div>
    </div>`;
}).join('');

const html = `<!doctype html>
<html lang="ru"><meta charset="utf-8">
<title>Шаблон слайда отдела — 6 блоков</title>
<style>
  body{margin:0;background:#e9edee;display:flex;justify-content:center;padding:24px;font-family:Arial,Helvetica,sans-serif}
  .slide{position:relative;width:${px(SLIDE_W)};height:${px(SLIDE_H)};background:#fff;box-shadow:0 2px 18px rgba(0,0,0,.12)}
  .dept{position:absolute;left:${px(MARGIN)};top:${px(0.38)};font-family:Georgia,'Times New Roman',serif;
        font-size:26pt;font-weight:700;color:#${INK};line-height:${px(0.55)}}
  .sub{position:absolute;right:${px(MARGIN)};top:${px(0.45)};font-size:9pt;color:#${MUTED};line-height:${px(0.4)}}
  .card{position:absolute;border-radius:14px;box-sizing:border-box;padding:${px(PAD)}}
  .head{display:flex;gap:${px(0.12)};align-items:flex-start;height:${px(HEAD_H)}}
  .badge{flex:0 0 auto;width:${px(BADGE)};height:${px(BADGE)};border-radius:50%;color:#fff;
         font-size:11pt;font-weight:700;display:flex;align-items:center;justify-content:center}
  .ct{font-size:11pt;font-weight:700;color:#${INK};line-height:1.05}
  .body{margin-top:${px(0.12)};position:relative}
  .r{display:flex;align-items:center;justify-content:space-between;height:${px(PITCH)}}
  .r.fact{justify-content:flex-start}
  .mn{font-size:9pt;color:#${MUTED};flex:0 0 42%}
  .r:not(.fact) .mn{flex:0 0 52%}
  .vl{font-size:9.5pt;font-weight:700}
  .r:not(.fact) .vl{flex:1;text-align:right}
  .r.fact .vl{flex:0 0 30%}
  .stt{font-size:9.5pt;font-weight:700;color:#${INK};flex:1;text-align:right}
  .driver{position:absolute;left:0;right:0;bottom:0}
  .dl{font-size:7.5pt;font-weight:700;letter-spacing:.06em;line-height:${px(0.2)}}
  .dt{font-size:9.5pt;color:#${INK};line-height:1.05}
  .li{font-size:9.5pt;color:#${INK};line-height:1.05;height:${px(0.44)};padding-left:14px;position:relative}
  .li::before{content:'•';position:absolute;left:0;color:#${INK}}
  .li.empty{height:${px(0.52)}}
</style>
<div class="slide">
  <div class="dept">Х отдел</div>
  <div class="sub">Руководитель отдела &middot; факт: 25.08–15.09.2026 &middot; цель — на квартал, до 30.09.2026</div>
  ${cards}
</div>
</html>`;

const htmlOut = path.join(__dirname, 'dept-template-6.html');
fs.writeFileSync(htmlOut, html);
console.log('OK →', htmlOut);
