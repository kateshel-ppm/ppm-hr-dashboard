/**
 * Добавляет в презентацию «Трекер ППМ Q3 2026» НОВЫЙ слайд-шаблон отдела
 * на шесть блоков, сетка 3×2:
 *
 *   1 Цель квартала
 *   2 Результаты на 15.09 и главный драйвер
 *   3 Что сделано за 3 недели
 *   4 Что не сделано, что ограничивает цель и где узкое горлышко
 *   5 Гипотезы и решения
 *   6 Приоритеты на 2 недели
 *
 * Существующие слайды не меняются: скрипт только дописывает один слайд в конец.
 *
 * Как запустить:
 *   1. script.google.com → «Новый проект», вставить этот файл целиком.
 *   2. Запустить функцию addTemplateSlide и разрешить доступ (Slides).
 *   3. В логе (Ctrl+Enter) будет ссылка на презентацию.
 *
 * Оформление повторяет карточки текущего шаблона; геометрия продублирована
 * в presentation/build-template-6.js (там же .pptx-версия слайда).
 */

// ── Настройки ───────────────────────────────────────────────────────────────

var DECK_URL = 'https://docs.google.com/presentation/d/1y9VZJlVc4xM_WjlryUWqAmcQtMjhfxDE31SRnit4bF4/edit';
var ALLOW_DUPLICATE = false;   // true — добавить слайд, даже если такой уже есть

// ── Палитра карточек ────────────────────────────────────────────────────────
var INK = '#2B3A55';
var MUTED = '#6B7785';
var SERIF = 'Georgia';
var SANS = 'Arial';

var BLOCKS = [
  { n: '1', title: 'Цель квартала',
    bg: '#EDF1FB', key: '#2B4C8C', kind: 'goal' },
  { n: '2', title: 'Результаты на 15.09 и главный драйвер',
    bg: '#EAF2EC', key: '#3E7D5A', kind: 'fact' },
  { n: '3', title: 'Что сделано за 3 недели',
    bg: '#E6F0F2', key: '#2F7382', kind: 'done' },
  { n: '4', title: 'Что не сделано, что ограничивает цель и где узкое горлышко',
    bg: '#FBEDEB', key: '#C0554A', kind: 'list' },
  { n: '5', title: 'Гипотезы и решения',
    bg: '#EDEBF7', key: '#5B4E9E', kind: 'list' },
  { n: '6', title: 'Приоритеты на 2 недели',
    bg: '#FBF3E4', key: '#C08420', kind: 'list' },
];

// ── Сетка, пункты (слайд 960 × 540) ─────────────────────────────────────────
var SLIDE_W = 960, SLIDE_H = 540;
var MARGIN = 36;
var GAP = 20.16;
var GRID_TOP = 90;
var COL_W = (SLIDE_W - MARGIN * 2 - GAP * 2) / 3;
var ROW1_H = 212.4;                                        // метрики и драйвер
var ROW2_H = SLIDE_H - GRID_TOP - MARGIN - GAP - ROW1_H;   // списки
var PAD = 18;
var BADGE = 21.6;
var HEAD_H = 37.44;
var PITCH = 21.6;
var INSET = 7.2;   // собственные поля текстового блока в Slides

// ── Точка входа ─────────────────────────────────────────────────────────────

function addTemplateSlide() {
  var deckId = DECK_URL.match(/[-\w]{25,}/)[0];
  var deck = SlidesApp.openById(deckId);

  if (!ALLOW_DUPLICATE && hasTemplate(deck)) {
    Logger.log('Такой слайд-шаблон уже есть — ничего не добавлено. ' +
               'Поставьте ALLOW_DUPLICATE = true, если нужна ещё одна копия.');
    return;
  }

  var slide = deck.appendSlide(SlidesApp.PredefinedLayout.BLANK);
  drawSlide(slide);

  Logger.log('Слайд добавлен в конец презентации (' + deck.getSlides().length + '-й).');
  Logger.log('Презентация: https://docs.google.com/presentation/d/' + deckId + '/edit');
}

function hasTemplate(deck) {
  var slides = deck.getSlides();
  for (var i = 0; i < slides.length; i++) {
    var els = slides[i].getPageElements();
    for (var j = 0; j < els.length; j++) {
      if (textOf(els[j]).indexOf('главный драйвер') !== -1) return true;
    }
  }
  return false;
}

// ── Отрисовка ───────────────────────────────────────────────────────────────

function drawSlide(slide) {
  text(slide, 'Х отдел', MARGIN, 27, 400, 40,
       { size: 26, bold: true, color: INK, font: SERIF, middle: true });
  text(slide, 'Руководитель отдела  ·  факт: 25.08–15.09.2026  ·  цель — на квартал, до 30.09.2026',
       SLIDE_W - MARGIN - 430, 32, 430, 29,
       { size: 9, color: MUTED, align: 'END', middle: true });

  for (var i = 0; i < BLOCKS.length; i++) {
    var b = BLOCKS[i];
    var x = MARGIN + (i % 3) * (COL_W + GAP);
    var y = i < 3 ? GRID_TOP : GRID_TOP + ROW1_H + GAP;
    var h = i < 3 ? ROW1_H : ROW2_H;

    var card = slide.insertShape(SlidesApp.ShapeType.ROUND_RECTANGLE, x, y, COL_W, h);
    card.getFill().setSolidFill(b.bg);
    card.getBorder().setTransparent();

    var badge = slide.insertShape(SlidesApp.ShapeType.ELLIPSE, x + PAD, y + PAD, BADGE, BADGE);
    badge.getFill().setSolidFill(b.key);
    badge.getBorder().setTransparent();
    badge.getText().setText(b.n);
    badge.getText().getTextStyle()
      .setFontSize(11).setBold(true).setForegroundColor('#FFFFFF').setFontFamily(SANS);
    badge.getText().getParagraphs()[0].getRange().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment.CENTER);
    badge.setContentAlignment(SlidesApp.ContentAlignment.MIDDLE);

    text(slide, b.title, x + PAD + BADGE + 8.6, y + PAD - 3,
         COL_W - PAD * 2 - BADGE - 8.6, HEAD_H,
         { size: 11, bold: true, color: INK });

    fillBlock(slide, b, x, y, h);
  }
}

function fillBlock(slide, b, x, y, h) {
  var cx = x + PAD;
  var cw = COL_W - PAD * 2;
  var top = y + PAD + HEAD_H + 8.6;
  var inner = h - PAD * 2 - HEAD_H - 8.6;
  var i;

  if (b.kind === 'goal' || b.kind === 'fact') {
    var isGoal = b.kind === 'goal';
    for (i = 0; i < 4; i++) {
      var ry = top + i * PITCH;
      text(slide, 'Метрика', cx, ry, cw * (isGoal ? 0.52 : 0.42), PITCH,
           { size: 9, color: MUTED, middle: true });
      text(slide, 'значение', cx + cw * (isGoal ? 0.52 : 0.42), ry,
           cw * (isGoal ? 0.48 : 0.3), PITCH,
           { size: 9.5, bold: true, color: b.key, middle: true,
             align: isGoal ? 'END' : 'START' });
      if (!isGoal) {
        text(slide, 'статус', cx + cw * 0.72, ry, cw * 0.28, PITCH,
             { size: 9.5, bold: true, color: INK, align: 'END', middle: true });
      }
    }

    if (!isGoal) {
      var dy = y + h - PAD - 40;
      text(slide, 'ГЛАВНЫЙ ДРАЙВЕР', cx, dy, cw, 14,
           { size: 7.5, bold: true, color: b.key, middle: true });
      text(slide, 'что именно вытянуло результат', cx, dy + 14, cw, 24,
           { size: 9.5, color: INK });
    }
    return;
  }

  if (b.kind === 'done') {
    var lines = [];
    for (i = 0; i < 4; i++) lines.push('Задача — результат');
    bulleted(slide, lines, cx, top, cw, inner);
    return;
  }

  bulleted(slide, [' ', ' ', ' '], cx, top, cw, inner);
}

// ── Вспомогательное ─────────────────────────────────────────────────────────

/** Текстовый блок; INSET гасит собственные поля Slides, чтобы текст встал по сетке. */
function text(slide, str, x, y, w, h, opts) {
  opts = opts || {};
  var tb = slide.insertTextBox(str, x - INSET, y, w + INSET * 2, h);
  var style = tb.getText().getTextStyle();
  style.setFontSize(opts.size || 10)
       .setBold(!!opts.bold)
       .setForegroundColor(opts.color || INK)
       .setFontFamily(opts.font || SANS);
  if (opts.align) {
    tb.getText().getParagraphs()[0].getRange().getParagraphStyle()
      .setParagraphAlignment(SlidesApp.ParagraphAlignment[opts.align]);
  }
  tb.setContentAlignment(opts.middle ? SlidesApp.ContentAlignment.MIDDLE
                                     : SlidesApp.ContentAlignment.TOP);
  return tb;
}

/** Маркированный список: пустые строки оставляют пустые пункты под заполнение. */
function bulleted(slide, lines, x, y, w, h) {
  var tb = slide.insertTextBox(lines.join('\n'), x - INSET, y, w + INSET * 2, h);
  tb.getText().getTextStyle()
    .setFontSize(9.5).setForegroundColor(INK).setFontFamily(SANS);
  tb.getText().getListStyle().applyListPreset(SlidesApp.ListPreset.DISC_CIRCLE_SQUARE);
  tb.setContentAlignment(SlidesApp.ContentAlignment.TOP);
  return tb;
}

function textOf(el) {
  try {
    if (el.getPageElementType() === SlidesApp.PageElementType.SHAPE) {
      return el.asShape().getText().asString();
    }
  } catch (e) { /* элемент без текста */ }
  return '';
}
