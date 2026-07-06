// Вход в HR Dashboard по коду на рабочую почту (OTP).
// Заменяет прежний общий пароль. Бэкенд — Google Apps Script (otp-backend.gs).
// Данные лежат в публичном репозитории — это защита ВХОДА, не самих данных.
(function () {
  var OTP = 'https://script.google.com/macros/s/AKfycbyi2TbWlKjEWN4cm0GBEMyrpSNIWg5vVe_LPaJ4_Cd7ax15pk0hvaZxFupecgT2gxQU8w/exec';
  var K = 'ppmAuthOtp';
  if (sessionStorage.getItem(K)) return; // уже вошёл в этой сессии
  try { document.documentElement.style.visibility = 'hidden'; } catch (e) {}

  function q(params) {
    var u = OTP + '?' + Object.keys(params).map(function (k) { return k + '=' + encodeURIComponent(params[k]); }).join('&');
    return fetch(u).then(function (r) { return r.json(); });
  }
  var ERR = {
    domain_not_allowed: 'Нужен рабочий email на @platipomiru.com',
    not_allowed: 'Этой почте доступ не открыт. Попроси HR добавить её.',
    rate_limit: 'Код уже отправлен — подожди минуту.',
    not_found: 'Сначала запроси код.',
    expired: 'Код истёк — запроси новый.',
    invalid_code: 'Неверный код.',
    too_many_attempts: 'Слишком много попыток — запроси новый код.'
  };
  function msg(e) { return ERR[e] || ('Ошибка: ' + e); }

  function build() {
    try { document.documentElement.style.visibility = ''; } catch (e) {}
    var o = document.createElement('div');
    o.id = '_otpgate';
    o.style.cssText = 'position:fixed;inset:0;z-index:2147483647;background:#0F172A;display:flex;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif';
    o.innerHTML =
      '<div style="background:#fff;padding:30px 28px;border-radius:16px;width:340px;box-shadow:0 12px 50px rgba(0,0,0,.35)">' +
      '<div style="font-weight:800;font-size:16px;color:#0F172A">HR Dashboard · Плати по миру</div>' +
      '<div id="_sub" style="color:#64748B;font-size:13px;margin:4px 0 16px">Вход по коду на рабочую почту</div>' +
      '<div id="_step1">' +
        '<input id="_em" type="email" placeholder="name@platipomiru.com" autocomplete="username" autofocus style="width:100%;height:42px;border:1px solid #E2E8F0;border-radius:10px;padding:0 12px;font-size:15px;outline:none;box-sizing:border-box">' +
        '<button id="_send" style="width:100%;height:42px;margin-top:10px;border:0;border-radius:10px;background:#2F6BFF;color:#fff;font-weight:700;font-size:15px;cursor:pointer">Получить код</button>' +
      '</div>' +
      '<div id="_step2" style="display:none">' +
        '<input id="_code" inputmode="numeric" maxlength="6" placeholder="6-значный код из письма" style="width:100%;height:42px;border:1px solid #E2E8F0;border-radius:10px;padding:0 12px;font-size:18px;letter-spacing:4px;text-align:center;outline:none;box-sizing:border-box">' +
        '<button id="_verify" style="width:100%;height:42px;margin-top:10px;border:0;border-radius:10px;background:#2F6BFF;color:#fff;font-weight:700;font-size:15px;cursor:pointer">Войти</button>' +
        '<div id="_back" style="text-align:center;margin-top:10px;font-size:12px;color:#64748B;cursor:pointer">← другой email</div>' +
      '</div>' +
      '<div id="_err" style="color:#E0454B;font-size:12px;min-height:15px;margin:9px 2px 0"></div>' +
      '</div>';
    document.body.appendChild(o);
    var er = document.getElementById('_err');
    var email = '';

    function busy(btn, on, txt) { btn.disabled = on; btn.textContent = on ? '…' : txt; }

    document.getElementById('_send').addEventListener('click', function () {
      email = (document.getElementById('_em').value || '').trim().toLowerCase();
      er.textContent = '';
      if (!/^[^@\s]+@platipomiru\.com$/.test(email)) { er.textContent = ERR.domain_not_allowed; return; }
      var b = this; busy(b, true, 'Получить код');
      q({ action: 'send', email: email }).then(function (d) {
        busy(b, false, 'Получить код');
        if (d.ok) {
          document.getElementById('_step1').style.display = 'none';
          document.getElementById('_step2').style.display = '';
          document.getElementById('_sub').textContent = 'Код отправлен на ' + email;
          document.getElementById('_code').focus();
        } else er.textContent = msg(d.error);
      }).catch(function () { busy(b, false, 'Получить код'); er.textContent = 'Нет связи с сервером входа.'; });
    });

    document.getElementById('_verify').addEventListener('click', function () {
      var code = (document.getElementById('_code').value || '').trim();
      er.textContent = '';
      var b = this; busy(b, true, 'Войти');
      q({ action: 'verify', email: email, code: code }).then(function (d) {
        if (d.ok) {
          try { sessionStorage.setItem(K, email); if (d.key) sessionStorage.setItem('ppmKey', d.key); } catch (e) {}
          location.reload(); // перезагрузка — чтобы данные догрузились уже с ключом расшифровки
        } else { busy(b, false, 'Войти'); er.textContent = msg(d.error) + (d.attempts_left != null ? ' Осталось попыток: ' + d.attempts_left : ''); }
      }).catch(function () { busy(b, false, 'Войти'); er.textContent = 'Нет связи с сервером входа.'; });
    });

    document.getElementById('_back').addEventListener('click', function () {
      document.getElementById('_step2').style.display = 'none';
      document.getElementById('_step1').style.display = '';
      document.getElementById('_sub').textContent = 'Вход по коду на рабочую почту';
      er.textContent = '';
    });
    document.getElementById('_code').addEventListener('keydown', function (e) { if (e.key === 'Enter') document.getElementById('_verify').click(); });
    document.getElementById('_em').addEventListener('keydown', function (e) { if (e.key === 'Enter') document.getElementById('_send').click(); });
  }

  if (document.body) build(); else document.addEventListener('DOMContentLoaded', build);
})();
