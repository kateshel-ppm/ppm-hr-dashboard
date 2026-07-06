// Плавающая кнопка «Обновить данные» на страницах дашборда.
// Появляется ТОЛЬКО если на этой машине запущена HR-админка (127.0.0.1:4477).
// Обычные посетители сайта её не видят (их localhost пуст). По клику — пересборка+публикация.
(function () {
  var ADMIN = 'http://127.0.0.1:4477';
  // проверяем, доступна ли админка
  var ctrl = new AbortController();
  var t = setTimeout(function () { ctrl.abort(); }, 2500);
  fetch(ADMIN + '/api/status', { signal: ctrl.signal })
    .then(function (r) { clearTimeout(t); if (r.ok) mount(); })
    .catch(function () { clearTimeout(t); });

  function mount() {
    var b = document.createElement('button');
    b.textContent = '⟳ Обновить данные';
    b.title = 'Пересобрать из Google Sheets и опубликовать';
    b.style.cssText = 'position:fixed;right:18px;bottom:18px;z-index:2147483000;background:#3B6FE0;color:#fff;border:0;border-radius:10px;padding:11px 16px;font-family:Inter,-apple-system,sans-serif;font-weight:700;font-size:13px;box-shadow:0 4px 16px rgba(0,0,0,.22);cursor:pointer';
    b.onmouseenter = function () { b.style.background = '#2F5BC7'; };
    b.onmouseleave = function () { if (!b.disabled) b.style.background = '#3B6FE0'; };
    document.body.appendChild(b);

    b.onclick = function () {
      if (!confirm('Пересобрать данные из Google Sheets и опубликовать дашборд?\nЗаймёт 1–3 минуты.')) return;
      b.disabled = true; b.style.background = '#9CA3AF'; b.textContent = '⏳ Обновляю… (1–3 мин)';
      fetch(ADMIN + '/api/refresh', { method: 'POST' })
        .then(function (r) { return r.json().then(function (d) { return { r: r, d: d }; }); })
        .then(function (x) {
          if (!x.r.ok || x.d.ok === false) throw new Error((x.d && x.d.error) || 'ошибка');
          b.style.background = '#12B76A'; b.textContent = '✓ Готово · сайт обновится ~2 мин';
          setTimeout(function () { location.reload(); }, 5000);
        })
        .catch(function (e) {
          b.disabled = false; b.style.background = '#F04438'; b.textContent = '✕ ' + (e.message || 'ошибка');
          setTimeout(function () { b.style.background = '#3B6FE0'; b.textContent = '⟳ Обновить данные'; }, 5000);
        });
    };
  }
})();
