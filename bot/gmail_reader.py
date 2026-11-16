"""Lee por IMAP los correos de Yelo y los marca con una etiqueta de Gmail al procesarlos.

La etiqueta hace de "memoria" del bot: así funciona igual en tu PC que en GitHub Actions,
donde cada ejecución empieza de cero. Los correos NO se marcan como leídos.
"""
import email
import imaplib
from dataclasses import dataclass
from email.header import decode_header, make_header

from . import config

ETIQUETA = "yelo-bot-procesado"


@dataclass
class Correo:
    uid: bytes
    asunto: str
    remitente: str
    html: str
    texto: str


def _decode(value: str | None) -> str:
    if not value:
        return ""
    return str(make_header(decode_header(value)))


def _cuerpos(msg: email.message.Message) -> tuple[str, str]:
    html, texto = "", ""
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition", "").startswith("attachment"):
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        contenido = payload.decode(charset, errors="replace")
        if part.get_content_type() == "text/html":
            html += contenido
        elif part.get_content_type() == "text/plain":
            texto += contenido
    return html, texto


def _conectar() -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(config.get("GMAIL_USER", required=True), config.get("GMAIL_APP_PASSWORD", required=True))
    imap.select("INBOX")
    return imap


def correos_yelo(incluir_procesados: bool = False) -> list[Correo]:
    consulta = f"from:{config.YELO_FROM} newer_than:{config.DIAS_ATRAS}d"
    if not incluir_procesados:
        consulta += f" -label:{ETIQUETA}"

    resultado: list[Correo] = []
    imap = _conectar()
    try:
        estado, data = imap.uid("SEARCH", "X-GM-RAW", f'"{consulta}"')
        if estado != "OK":
            return resultado
        for uid in data[0].split():
            # BODY.PEEK: no marca el correo como leído
            estado, partes = imap.uid("FETCH", uid, "(BODY.PEEK[])")
            if estado != "OK" or not partes or partes[0] is None:
                continue
            msg = email.message_from_bytes(partes[0][1])
            html, texto = _cuerpos(msg)
            resultado.append(Correo(uid, _decode(msg.get("Subject")), _decode(msg.get("From")), html, texto))
    finally:
        imap.logout()
    return resultado


def marcar_procesado(uids: list[bytes]) -> None:
    if not uids:
        return
    imap = _conectar()
    try:
        imap.create(ETIQUETA)  # si ya existe, Gmail devuelve error y no pasa nada
        for uid in uids:
            imap.uid("STORE", uid, "+X-GM-LABELS", f'"{ETIQUETA}"')
    finally:
        imap.logout()
