/**
 * Перестраивает слайды-шаблоны презентации «Трекер ППМ Q3 2026»
 * под сквозную нумерацию 1–6:
 *
 *   1  Цель квартала                        (без изменений)
 *   2  Результат на 15.09                   (без изменений)
 *   3  Что сделал и что помогло (драйвер)   ← новый блок
 *   4  Что не сделал и узкое горлышко       ← бывший «Что ограничивает цель»
 *   5  Гипотезы и решения                   (перенумерован с 4)
 *   6  Приоритеты на 2 недели               (перенумерован с 5)
 *
 * Как запустить:
 *   1. script.google.com → «Новый проект», вставить этот файл целиком.
 *   2. Запустить функцию updateDeptSlides и разрешить доступ (Slides + Drive).
 *   3. В логе (Ctrl+Enter) будет ссылка на результат.
 *
 * По умолчанию скрипт работает НА КОПИИ презентации — оригинал не меняется.
 * Когда результат устроит, поставьте WORK_ON_COPY = false и запустите ещё раз.
 *
 * Что делает на каждом слайде-шаблоне:
 *   - находит блоки «2 Результат на 15.09» и «3 Что ограничивает цель»;
 *   - считает шаг колонки и ужимает все блоки по горизонтали так, чтобы
 *     вместо пяти колонок поместилось шесть (шрифты не трогаются);
 *   - в освободившееся место справа от блока 2 копирует оформление
 *     соседнего блока и подставляет текст нового блока 3;
 *   - переписывает заголовок бывшего блока 3 и перенумеровывает 3→4, 4→5, 5→6.
 *
 * Две ветки:
 *   - если блок «2.1» уже добавлен вручную — скрипт только перенумеровывает
 *     (2.1→3, 3→4, 4→5, 5→6) и меняет заголовки, геометрию не трогает;
 *   - если блоков пять — вставляет новый блок 3 и перенумеровывает остальные.
 *
 * Тексты внутри заполненных блоков не перезаписываются: подставляются только
 * пустые места шаблона. Скрипт идемпотентный: перестроенный слайд пропускается.
 */

// ── Настройки ───────────────────────────────────────────────────────────────

var DECK_URL = 'https://docs.google.com/presentation/d/1y9VZJlVc4xM_WjlryUWqAmcQtMjhfxDE31SRnit4bF4/edit';

var WORK_ON_COPY = true;   // true — править копию, false — оригинал
var DRY_RUN = false;       // true — только показать в логе, что будет сделано

// Опорные тексты существующего шаблона
var ANCHOR_2 = 'Результат на 15.09';   // заголовок блока 2
var ANCHOR_3 = 'ограничивает';         // заголовок блока 3 (станет блоком 4)
var ANCHOR_4 = 'Гипотезы';             // заголовок блока 4 (станет блоком 5)
var ANCHOR_5 = 'Приоритеты';           // заголовок блока 5 (станет блоком 6)
var ANCHOR_21 = 'сделано за 3 недели'; // блок «2.1», если он уже добавлен вручную

// Новый блок 3
var NEW_TITLE = 'Что сделал и что помогло (драйвер)';
var NEW_BODY = [
  'Задача — результат',
  'драйвер: что помогло',
  '',
  'Задача — результат',
  'драйвер: что помогло',
  '',
  'Задача — результат',
  'драйвер: что помогло',
  '',
  'Задача — результат',
  'драйвер: что помогло'
].join('\n');

// Бывший блок 3 → блок 4
var TITLE_4 = 'Что не сделал и узкое горлышко';
var BODY_4 = [
  'Задача — почему не сделана',
  'узкое горлышко: что мешает',
  '',
  'Задача — почему не сделана',
  'узкое горлышко: что мешает',
  '',
  'Задача — почему не сделана',
  'узкое горлышко: что мешает'
].join('\n');

// ── Точка входа ─────────────────────────────────────────────────────────────

function updateDeptSlides() {
  var srcId = DECK_URL.match(/[-\w]{25,}/)[0];
  var deckId = srcId;

  if (WORK_ON_COPY && !DRY_RUN) {
    var copy = DriveApp.getFileById(srcId).makeCopy('Трекер ППМ Q3 2026 — блоки 1–6');
    deckId = copy.getId();
    Logger.log('Работаем на копии: https://docs.google.com/presentation/d/' + deckId + '/edit');
  }

  var deck = SlidesApp.openById(deckId);
  var slides = deck.getSlides();
  var changed = 0;

  for (var i = 0; i < slides.length; i++) {
    if (processSlide(slides[i], i + 1)) changed++;
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

  if (findByText(els, NEW_TITLE) || findByText(els, TITLE_4)) {
    Logger.log('Слайд ' + num + ': уже перестроен — пропускаем.');
    return false;
  }

  var title3 = findByText(els, ANCHOR_3);
  if (!title3) {
    Logger.log('Слайд ' + num + ': не найден блок «Что ограничивает цель» — пропускаем.');
    return false;
  }
  var title4 = findByText(els, ANCHOR_4);
  var title5 = findByText(els, ANCHOR_5);

  var badge2 = findBadge(els, '2', title2);
  var badge3 = findBadge(els, '3', title3);
  var badge4 = title4 ? findBadge(els, '4', title4) : null;
  var badge5 = title5 ? findBadge(els, '5', title5) : null;

  // Ветка А: блок 2.1 уже добавлен вручную — только перенумеровать и переназвать,
  // геометрию и тексты внутри блоков не трогаем.
  var title21 = findByText(els, ANCHOR_21);
  if (title21) {
    Logger.log('Слайд ' + num + ': блок 2.1 уже есть — только перенумерация 2.1→3, 3→4, 4→5, 5→6.');
    if (DRY_RUN) return true;

    var badge21 = findBadge(els, '2.1', title21);
    setText(title21, NEW_TITLE);
    if (badge21) {
      setText(badge21, '3');
    } else {
      Logger.log('  · кружок «2.1» не найден — поправьте номер вручную.');
    }
    renumber(badge3, badge4, badge5, title3);
    return true;
  }

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

  // Элементы колонки 3 запоминаем до трансформации — с них снимем оформление
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

  // 2. Новый блок 3 — копия оформления соседнего блока, сдвинутая влево
  var dx = pitch * f;
  for (var m = 0; m < col3Els.length; m++) {
    var src = col3Els[m];
    var dup = src.duplicate();
    dup.setLeft(src.getLeft() - dx);
    dup.setTop(src.getTop());
    dup.setWidth(src.getWidth());
    dup.setHeight(src.getHeight());

    if (badge3 && src.getObjectId() === badge3.getObjectId()) {
      setText(dup, '3');
    } else if (src.getObjectId() === title3.getObjectId()) {
      setText(dup, NEW_TITLE);
    } else if (textOf(src).replace(/\s/g, '') !== '') {
      setText(dup, NEW_BODY);
    }
  }

  // 3. Сквозная нумерация: бывшие 3, 4, 5 становятся 4, 5, 6
  renumber(badge3, badge4, badge5, title3);

  // 4. Тело бывшего блока 3 — под новый смысл «что не сделал».
  //    Заполненные блоки не трогаем: там реальный текст отдела.
  for (var n = 0; n < col3Els.length; n++) {
    var e3 = col3Els[n];
    if (badge3 && e3.getObjectId() === badge3.getObjectId()) continue;
    if (e3.getObjectId() === title3.getObjectId()) continue;
    if (isPlaceholder(textOf(e3))) setText(e3, BODY_4);
  }

  return true;
}

/** Бывшие блоки 3, 4, 5 становятся 4, 5, 6; заголовок блока 3 меняет смысл. */
function renumber(badge3, badge4, badge5, title3) {
  setText(title3, TITLE_4);
  if (badge3) setText(badge3, '4');
  if (badge4) setText(badge4, '5');
  if (badge5) setText(badge5, '6');
  if (!badge3 || !badge4 || !badge5) {
    Logger.log('  · часть номеров найти не удалось — проверьте нумерацию вручную.');
  }
}

/** Пустой блок шаблона: ничего, кроме пробелов и прочерков. */
function isPlaceholder(text) {
  return text.replace(/[\s\u2014\u2013-]/g, '') === '';
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
