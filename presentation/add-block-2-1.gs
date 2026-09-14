/**
 * Добавляет блок «2.1 Что было сделано за 3 недели» на слайды-шаблоны
 * презентации «Трекер ППМ Q3 2026» — сразу справа от блока
 * «2 Результат на 15.09».
 *
 * Как запустить:
 *   1. script.google.com → «Новый проект», вставить этот файл целиком.
 *   2. Запустить функцию addBlock21 и разрешить доступ (Slides + Drive).
 *   3. В логе (Ctrl+Enter) будет ссылка на результат.
 *
 * По умолчанию скрипт работает НА КОПИИ презентации — оригинал не меняется.
 * Когда результат устроит, поставьте WORK_ON_COPY = false и запустите ещё раз,
 * чтобы правка легла в исходный файл.
 *
 * Что делает на каждом слайде-шаблоне:
 *   - находит блоки «2 Результат на 15.09» и «3 Что ограничивает цель»;
 *   - считает шаг колонки и ужимает все блоки по горизонтали так, чтобы
 *     вместо пяти колонок поместилось шесть (пропорции и шрифты не трогаются);
 *   - в освободившееся место справа от блока 2 копирует оформление блока 3
 *     (кружок с номером, заголовок, тело) и подставляет новый текст.
 *
 * Скрипт идемпотентный: слайд, на котором блок 2.1 уже есть, пропускается.
 */

// ── Настройки ───────────────────────────────────────────────────────────────

var DECK_URL = 'https://docs.google.com/presentation/d/1y9VZJlVc4xM_WjlryUWqAmcQtMjhfxDE31SRnit4bF4/edit';

var WORK_ON_COPY = true;   // true — править копию, false — оригинал
var DRY_RUN = false;       // true — только показать в логе, что будет сделано

var ANCHOR_2 = 'Результат на 15.09';   // текст заголовка блока 2
var ANCHOR_3 = 'ограничивает';         // часть заголовка блока 3
var BADGE_3 = '3';                     // номер блока 3 (кружок)

var NEW_BADGE = '2.1';
var NEW_TITLE = 'Что было сделано за 3 недели';
var NEW_BODY = [
  'Задача — результат',
  'Задача — результат',
  'Задача — результат',
  'Задача — результат',
  'Задача — результат'
].join('\n');

// ── Точка входа ─────────────────────────────────────────────────────────────

function addBlock21() {
  var srcId = DECK_URL.match(/[-\w]{25,}/)[0];
  var deckId = srcId;

  if (WORK_ON_COPY && !DRY_RUN) {
    var copy = DriveApp.getFileById(srcId).makeCopy('Трекер ППМ Q3 2026 — с блоком 2.1');
    deckId = copy.getId();
    Logger.log('Работаем на копии: https://docs.google.com/presentation/d/' + deckId + '/edit');
  }

  var deck = SlidesApp.openById(deckId);
  var slides = deck.getSlides();
  var changed = 0;

  for (var i = 0; i < slides.length; i++) {
    var res = processSlide(slides[i], i + 1);
    if (res) changed++;
  }

  Logger.log('Готово. Слайдов обработано: ' + changed + ' из ' + slides.length +
             (DRY_RUN ? ' (DRY_RUN — ничего не сохранено)' : ''));
  if (!DRY_RUN) {
    Logger.log('Результат: https://docs.google.com/presentation/d/' + deckId + '/edit');
  }
}

// ── Обработка одного слайда ─────────────────────────────────────────────────

function processSlide(slide, num) {
  var els = slide.getPageElements();

  var title2 = findByText(els, ANCHOR_2);
  if (!title2) return false;                       // не слайд-шаблон

  if (findByText(els, NEW_TITLE)) {
    Logger.log('Слайд ' + num + ': блок 2.1 уже есть — пропускаем.');
    return false;
  }

  var title3 = findByText(els, ANCHOR_3);
  if (!title3) {
    Logger.log('Слайд ' + num + ': не найден блок «Что ограничивает цель» — пропускаем.');
    return false;
  }

  var badge2 = findBadge(els, '2', title2);
  var badge3 = findBadge(els, BADGE_3, title3);

  var col2Left = badge2 ? Math.min(badge2.getLeft(), title2.getLeft()) : title2.getLeft();
  var col3Left = badge3 ? Math.min(badge3.getLeft(), title3.getLeft()) : title3.getLeft();

  var pitch = col3Left - col2Left;                 // шаг колонки, pt
  if (pitch < 40) {
    Logger.log('Слайд ' + num + ': не удалось определить шаг колонок (' +
               Math.round(pitch) + ' pt) — пропускаем.');
    return false;
  }

  // Границы содержимого слайда
  var contentLeft = Infinity;
  var contentRight = -Infinity;
  for (var i = 0; i < els.length; i++) {
    contentLeft = Math.min(contentLeft, els[i].getLeft());
    contentRight = Math.max(contentRight, els[i].getLeft() + els[i].getWidth());
  }
  var contentW = contentRight - contentLeft;
  var f = contentW / (contentW + pitch);           // коэффициент сжатия

  Logger.log('Слайд ' + num + ': шаг колонки ' + Math.round(pitch) +
             ' pt, сжатие до ' + Math.round(f * 100) + '%.');
  if (DRY_RUN) return true;

  // Элементы колонки 3 запоминаем до трансформации
  var col3Els = [];
  for (var j = 0; j < els.length; j++) {
    var l = els[j].getLeft();
    if (l >= col3Left - 4 && l < col3Left + pitch - 4) col3Els.push(els[j]);
  }

  // 1. Сжимаем всё по горизонтали; блоки 3–5 дополнительно сдвигаем вправо
  var cut = col3Left - 4;
  for (var k = 0; k < els.length; k++) {
    var el = els[k];
    var left = el.getLeft();
    var shift = (left >= cut) ? pitch : 0;
    var newLeft = contentLeft + (left - contentLeft + shift) * f;
    var newWidth = el.getWidth() * f;

    el.setLeft(newLeft);
    if (newWidth >= 1) {
      try {
        el.setWidth(newWidth);
      } catch (e) {
        Logger.log('  · ширину элемента изменить не удалось (' + e.message + ') — оставлена прежней.');
      }
    }
  }

  // 2. Копируем оформление блока 3 на освободившееся место
  var dx = pitch * f;                              // на столько сдвигаем копии влево
  for (var m = 0; m < col3Els.length; m++) {
    var src = col3Els[m];
    var dup = src.duplicate();
    dup.setLeft(src.getLeft() - dx);
    dup.setTop(src.getTop());
    dup.setWidth(src.getWidth());
    dup.setHeight(src.getHeight());

    if (badge3 && src.getObjectId() === badge3.getObjectId()) {
      setText(dup, NEW_BADGE);
    } else if (src.getObjectId() === title3.getObjectId()) {
      setText(dup, NEW_TITLE);
    } else if (textOf(src).replace(/\s/g, '') !== '') {
      setText(dup, NEW_BODY);
    }
  }

  return true;
}

// ── Вспомогательное ─────────────────────────────────────────────────────────

function textOf(el) {
  try {
    if (el.getPageElementType() === SlidesApp.PageElementType.SHAPE) {
      return el.asShape().getText().asString();
    }
  } catch (e) { /* элемент без текста */ }
  return '';
}

function setText(el, value) {
  try {
    el.asShape().getText().setText(value);
  } catch (e) {
    Logger.log('  · текст задать не удалось: ' + e.message);
  }
}

function findByText(els, needle) {
  for (var i = 0; i < els.length; i++) {
    if (textOf(els[i]).indexOf(needle) !== -1) return els[i];
  }
  return null;
}

/** Кружок с номером блока: тот же текст, левее заголовка и на той же высоте. */
function findBadge(els, label, title) {
  var titleMidY = title.getTop() + title.getHeight() / 2;
  var best = null;
  var bestDist = Infinity;

  for (var i = 0; i < els.length; i++) {
    var el = els[i];
    if (textOf(el).replace(/\s/g, '') !== label) continue;
    if (el.getLeft() > title.getLeft() + 2) continue;

    var midY = el.getTop() + el.getHeight() / 2;
    var dist = Math.abs(midY - titleMidY);
    if (dist > title.getHeight() + 24) continue;
    if (dist < bestDist) { best = el; bestDist = dist; }
  }
  return best;
}
