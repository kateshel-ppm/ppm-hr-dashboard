// Общая расшифровка зашифрованных данных (ключ из входа по коду — sessionStorage.ppmKey).
window.ppmDecrypt = async function (blob, keyB64) {
  if (!keyB64) throw new Error('нет ключа (нужен вход)');
  function b64(b) {
    var s = b.replace(/-/g, '+').replace(/_/g, '/');
    var bin = atob(s), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a;
  }
  var p = blob.split(':');
  var key = await crypto.subtle.importKey('raw', b64(keyB64), 'AES-GCM', false, ['decrypt']);
  var pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64(p[0]) }, key, b64(p[1]));
  return JSON.parse(new TextDecoder().decode(pt));
};
window.ppmLoad = function (file) {
  var key = sessionStorage.getItem('ppmKey');
  return fetch(file + '?v=' + Date.now(), { cache: 'no-store' })
    .then(function (r) { return r.text(); })
    .then(function (t) { return window.ppmDecrypt(t, key); });
};
