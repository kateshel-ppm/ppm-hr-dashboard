#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Прямая правка Google Таблицы через Sheets API v4 и сервисный аккаунт.

Учётные данные берутся из окружения (в чат их присылать не нужно):
    GOOGLE_SA_KEY       — содержимое JSON-ключа сервисного аккаунта, одной строкой
    GOOGLE_SA_KEY_FILE  — либо путь к файлу с этим JSON

Использование:
    python3 sheets_write.py tabs   <spreadsheet_id>
    python3 sheets_write.py read   <spreadsheet_id> "<Имя вкладки>"
    python3 sheets_write.py write  <spreadsheet_id> "<Имя вкладки>" data.csv
    python3 sheets_write.py append <spreadsheet_id> "<Имя вкладки>" data.csv

`write` создаёт вкладку, если её нет, очищает и записывает CSV целиком.
`append` дописывает строки в конец, ничего не затирая.
"""

import base64
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://sheets.googleapis.com/v4/spreadsheets"
SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def load_credentials() -> dict:
    raw = os.environ.get("GOOGLE_SA_KEY")
    if not raw:
        path = os.environ.get("GOOGLE_SA_KEY_FILE")
        if not path:
            sys.exit(
                "Нет учётных данных: задайте GOOGLE_SA_KEY (JSON одной строкой) "
                "или GOOGLE_SA_KEY_FILE (путь к JSON-ключу)."
            )
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.exit(f"Ключ сервисного аккаунта не разбирается как JSON: {exc}")


def access_token(creds: dict) -> str:
    """JWT-bearer flow: подписываем утверждение ключом сервисного аккаунта."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        sys.exit("Нужен пакет cryptography:  pip install cryptography")

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": creds["client_email"],
        "scope": SCOPE,
        "aud": TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
    }
    signing_input = f"{_b64(json.dumps(header).encode())}.{_b64(json.dumps(claims).encode())}".encode()

    key = serialization.load_pem_private_key(creds["private_key"].encode(), password=None)
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    assertion = f"{signing_input.decode()}.{_b64(signature)}"

    body = urllib.parse.urlencode(
        {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}
    ).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=body)) as resp:
            return json.load(resp)["access_token"]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        sys.exit(
            f"Не удалось получить токен ({exc.code}). Проверьте, что ключ сервисного "
            f"аккаунта действующий и что Google Sheets API включён в проекте.\n{detail}"
        )


def call(token: str, method: str, path: str, payload=None):
    url = f"{API}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        sys.exit(f"Sheets API вернул {exc.code}:\n{detail}")


def get_tabs(token: str, sid: str) -> dict:
    meta = call(token, "GET", f"{sid}?fields=sheets.properties")
    return {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta.get("sheets", [])}


def ensure_tab(token: str, sid: str, title: str) -> None:
    if title in get_tabs(token, sid):
        return
    call(token, "POST", f"{sid}:batchUpdate",
         {"requests": [{"addSheet": {"properties": {"title": title}}}]})
    print(f"Создана вкладка «{title}»")


def read_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [row for row in csv.reader(fh)]


def quote(title: str) -> str:
    return urllib.parse.quote(f"'{title.replace(chr(39), chr(39) * 2)}'", safe="")


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, sid = sys.argv[1], sys.argv[2]
    token = access_token(load_credentials())

    if cmd == "tabs":
        for name in get_tabs(token, sid):
            print(name)
        return

    if len(sys.argv) < 4:
        sys.exit("Укажите имя вкладки.")
    tab = sys.argv[3]

    if cmd == "read":
        res = call(token, "GET", f"{sid}/values/{quote(tab)}")
        for row in res.get("values", []):
            print("\t".join(row))
        return

    if cmd not in ("write", "append"):
        sys.exit(f"Неизвестная команда: {cmd}")
    if len(sys.argv) < 5:
        sys.exit("Укажите путь к CSV-файлу.")

    values = read_csv(sys.argv[4])
    ensure_tab(token, sid, tab)

    if cmd == "write":
        call(token, "POST", f"{sid}/values/{quote(tab)}:clear", {})
        res = call(token, "PUT",
                   f"{sid}/values/{quote(tab)}?valueInputOption=USER_ENTERED",
                   {"values": values})
        print(f"Записано ячеек: {res.get('updatedCells')} в «{tab}»")
    else:
        res = call(token, "POST",
                   f"{sid}/values/{quote(tab)}:append"
                   "?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS",
                   {"values": values})
        print(f"Дописано ячеек: {res.get('updates', {}).get('updatedCells')} в «{tab}»")


if __name__ == "__main__":
    main()
