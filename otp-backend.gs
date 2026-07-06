/**
 * HR Dashboard — OTP Backend
 * Google Apps Script Web App
 * Деплоить как: "Anyone" can access, Execute as: "Me"
 *
 * Endpoints (GET):
 *   ?action=send&email=name@platipomiru.com   — отправить код
 *   ?action=verify&email=...&code=123456      — проверить код
 */

const ALLOWED_DOMAIN = '@platipomiru.com';
const CODE_TTL_MS    = 10 * 60 * 1000;   // 10 минут
const MAX_ATTEMPTS   = 5;                 // макс попыток ввода

function doGet(e) {
  const action = (e.parameter.action || '').trim();
  const email  = (e.parameter.email  || '').toLowerCase().trim();
  const props  = PropertiesService.getScriptProperties();

  // ── ADMIN: управление белым списком email (защита секретом ADMIN_SECRET) ──
  //   ?action=admin&secret=...&op=list                 — список разрешённых
  //   ?action=admin&secret=...&op=add&email=...        — добавить доступ
  //   ?action=admin&secret=...&op=remove&email=...     — отозвать доступ
  if (action === 'admin') {
    const secret = props.getProperty('ADMIN_SECRET') || '';
    if (!secret || (e.parameter.secret || '') !== secret) {
      return json({ ok: false, error: 'forbidden' });
    }
    const op = (e.parameter.op || 'list').trim();
    if (op === 'setkey') { props.setProperty('DATA_KEY', e.parameter.key || ''); return json({ ok: true }); }
    let list = getAllowlist(props);
    if (op === 'add' && email)      { if (!list.includes(email)) list.push(email); setAllowlist(props, list); }
    else if (op === 'remove' && email) { list = list.filter(x => x !== email);      setAllowlist(props, list); }
    return json({ ok: true, list });
  }

  // Проверка рабочего домена (для send/verify)
  if (!email.endsWith(ALLOWED_DOMAIN)) {
    return json({ ok: false, error: 'domain_not_allowed' });
  }

  // Белый список: если он задан — email обязан быть в нём.
  // Пока список пуст — пускаем любой @platipomiru.com (чтобы не запереть себя до первого добавления).
  const allow = getAllowlist(props);
  if (allow.length && !allow.includes(email)) {
    return json({ ok: false, error: 'not_allowed' });
  }

  // ── SEND ──────────────────────────────────────────────────────────────────
  if (action === 'send') {
    // Rate limit: не чаще раза в минуту
    const lastSent = parseInt(props.getProperty(`sent_${email}`) || '0');
    if (Date.now() - lastSent < 60_000) {
      return json({ ok: false, error: 'rate_limit', retry_in: 60 });
    }

    const code    = pad6(Math.floor(Math.random() * 1_000_000));
    const expires = Date.now() + CODE_TTL_MS;

    props.setProperty(`otp_${email}`,  JSON.stringify({ code, expires, attempts: 0 }));
    props.setProperty(`sent_${email}`, String(Date.now()));

    MailApp.sendEmail({
      to:      email,
      subject: `${code} — ваш код входа в HR Dashboard`,
      body:
        `Добрый день!\n\n` +
        `Код для входа в HR Dashboard:\n\n` +
        `  ${code}\n\n` +
        `Код действует 10 минут.\n\n` +
        `Если вы не запрашивали код — проигнорируйте это письмо.\n\n` +
        `── HR Dashboard / ГлобалПэй`,
      htmlBody:
        `<div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;background:#f2f3f7;border-radius:16px">` +
        `<div style="background:#fff;border-radius:12px;padding:32px;text-align:center">` +
        `<div style="width:48px;height:48px;background:#3B6FE0;border-radius:12px;display:inline-flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;color:#fff;margin-bottom:20px">HR</div>` +
        `<h2 style="font-size:20px;font-weight:700;color:#0A0B0D;margin:0 0 8px">Код входа в HR Dashboard</h2>` +
        `<p style="color:#6B7280;font-size:14px;margin:0 0 28px">Введите этот код на странице входа</p>` +
        `<div style="background:#EBF1FD;border-radius:12px;padding:20px;margin-bottom:24px">` +
        `<span style="font-size:36px;font-weight:800;color:#3B6FE0;letter-spacing:8px">${code}</span>` +
        `</div>` +
        `<p style="color:#9CA3AF;font-size:12px;margin:0">Код действует 10 минут · Только для @platipomiru.com</p>` +
        `</div></div>`,
    });

    return json({ ok: true });
  }

  // ── VERIFY ────────────────────────────────────────────────────────────────
  if (action === 'verify') {
    const inputCode = (e.parameter.code || '').trim();
    const stored    = props.getProperty(`otp_${email}`);

    if (!stored) return json({ ok: false, error: 'not_found' });

    const entry = JSON.parse(stored);

    if (Date.now() > entry.expires) {
      props.deleteProperty(`otp_${email}`);
      return json({ ok: false, error: 'expired' });
    }

    entry.attempts = (entry.attempts || 0) + 1;
    if (entry.attempts > MAX_ATTEMPTS) {
      props.deleteProperty(`otp_${email}`);
      return json({ ok: false, error: 'too_many_attempts' });
    }

    if (entry.code !== inputCode) {
      props.setProperty(`otp_${email}`, JSON.stringify(entry));
      return json({ ok: false, error: 'invalid_code', attempts_left: MAX_ATTEMPTS - entry.attempts });
    }

    // Успех — удаляем код и выдаём ключ расшифровки данных
    props.deleteProperty(`otp_${email}`);
    props.deleteProperty(`sent_${email}`);
    return json({ ok: true, email, key: props.getProperty('DATA_KEY') || '' });
  }

  return json({ ok: false, error: 'unknown_action' });
}

// ── helpers ────────────────────────────────────────────────────────────────
function getAllowlist(props) {
  try { return JSON.parse(props.getProperty('ALLOWLIST') || '[]'); } catch (e) { return []; }
}
function setAllowlist(props, list) {
  props.setProperty('ALLOWLIST', JSON.stringify(list.map(x => x.toLowerCase().trim()).filter(Boolean)));
}

function pad6(n) {
  return String(n).padStart(6, '0');
}

function json(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
