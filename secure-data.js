// Прозрачная расшифровка данных с именами. Подключается на «Структуре».
// Страница как обычно делает fetch('org_structure.json'), а этот шим отдаёт
// расшифрованные данные из secure/struktura.enc (ключ — из входа по коду, sessionStorage.ppmKey).
(function () {
  function b64ToBytes(b64) {
    var s = b64.replace(/-/g, '+').replace(/_/g, '/');
    var bin = atob(s);
    var a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a;
  }
  async function ppmDecrypt(blob, keyB64) {
    if (!keyB64) throw new Error('нет ключа (нужен вход)');
    var parts = blob.split(':');
    var iv = b64ToBytes(parts[0]);
    var ct = b64ToBytes(parts[1]);
    var raw = b64ToBytes(keyB64);
    var key = await crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['decrypt']);
    var pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: iv }, key, ct);
    return JSON.parse(new TextDecoder().decode(pt));
  }
  var cache = null;
  var _fetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    if (typeof url === 'string' && url.indexOf('org_structure.json') === 0) {
      var p = cache
        ? Promise.resolve(cache)
        : _fetch('secure/struktura.enc?v=' + Date.now(), { cache: 'no-store' })
            .then(function (r) { return r.text(); })
            .then(function (t) { return ppmDecrypt(t, sessionStorage.getItem('ppmKey')); })
            .then(function (arr) { cache = arr; return arr; });
      return p.then(function (arr) {
        return new Response(JSON.stringify(arr), { headers: { 'Content-Type': 'application/json' } });
      });
    }
    return _fetch(url, opts);
  };
})();
