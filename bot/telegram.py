"""Envío de avisos por Telegram (API oficial de bots)."""
import html

import requests

from . import config

API = "https://api.telegram.org/bot{token}/{metodo}"


def _url(metodo: str) -> str:
    token = config.get("TELEGRAM_BOT_TOKEN", required=True)
    return API.format(token=token, metodo=metodo)


def esc(texto: str) -> str:
    return html.escape(texto or "")


def enviar(mensaje_html: str, boton: tuple[str, str] | None = None) -> None:
    datos = {
        "chat_id": config.get("TELEGRAM_CHAT_ID", required=True),
        "text": mensaje_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if boton:
        datos["reply_markup"] = {"inline_keyboard": [[{"text": boton[0], "url": boton[1]}]]}
    r = requests.post(_url("sendMessage"), json=datos, timeout=15)
    r.raise_for_status()


def enviar_foto(ruta: str, pie: str = "") -> None:
    with open(ruta, "rb") as f:
        r = requests.post(
            _url("sendPhoto"),
            data={"chat_id": config.get("TELEGRAM_CHAT_ID", required=True), "caption": pie[:1000]},
            files={"photo": f},
            timeout=30,
        )
    r.raise_for_status()


def obtener_chat_ids() -> list[tuple[int, str]]:
    r = requests.get(_url("getUpdates"), timeout=15)
    r.raise_for_status()
    vistos = {}
    for upd in r.json().get("result", []):
        chat = (upd.get("message") or {}).get("chat")
        if chat:
            vistos[chat["id"]] = chat.get("first_name") or chat.get("title") or ""
    return list(vistos.items())
