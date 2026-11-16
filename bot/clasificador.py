"""Encuentra el botón "Lista GRATIS" en el correo y decide si es Xceed, Dice o un código."""
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

XCEED, DICE_LINK, DICE_CODIGO, DESCONOCIDO = "xceed", "dice_link", "dice_codigo", "desconocido"

_LISTA_RE = re.compile(r"lista\s+(gratis|free)", re.I)
_FECHA_RE = re.compile(r"(\d{1,2}/\d{1,2})")
# "código: YELO2711", "codigo YELO2711", "code: ABC123"
_CODIGO_RE = re.compile(r"c[oó]digo\s*(?:de\s+dice)?\s*[:\-]?\s*([A-Z0-9]{4,20})\b", re.I)


@dataclass
class Lista:
    tipo: str
    fecha: str | None
    url: str | None = None
    codigo: str | None = None
    texto_boton: str | None = None


def _resolver(url: str) -> str:
    """Sigue redirecciones de enlaces de seguimiento de la newsletter."""
    try:
        r = requests.get(url, allow_redirects=True, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        return r.url
    except requests.RequestException:
        return url


def _tipo_por_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "xceed" in host:
        return XCEED
    if "dice.fm" in host:
        return DICE_LINK
    return DESCONOCIDO


def clasificar(html: str, texto: str = "", resolver_links: bool = True) -> Lista | None:
    soup = BeautifulSoup(html or "", "html.parser")
    texto_plano = soup.get_text(" ", strip=True) if html else texto

    for a in soup.find_all("a", href=True):
        etiqueta = a.get_text(" ", strip=True)
        if not _LISTA_RE.search(etiqueta):
            continue
        fecha = (_FECHA_RE.search(etiqueta) or [None, None])[1]
        url = _resolver(a["href"]) if resolver_links else a["href"]
        tipo = _tipo_por_url(url)
        if tipo != DESCONOCIDO:
            return Lista(tipo=tipo, fecha=fecha, url=url, texto_boton=etiqueta)
        # Si el botón no lleva a Xceed/Dice, quizá el código está en el correo
        codigo = _CODIGO_RE.search(texto_plano)
        if codigo:
            return Lista(DICE_CODIGO, fecha, url=url, codigo=codigo.group(1), texto_boton=etiqueta)
        return Lista(DESCONOCIDO, fecha, url=url, texto_boton=etiqueta)

    # Sin botón: buscar mención a lista gratis + código en el texto
    if _LISTA_RE.search(texto_plano):
        codigo = _CODIGO_RE.search(texto_plano)
        fecha = (_FECHA_RE.search(texto_plano) or [None, None])[1]
        dice = next((a["href"] for a in soup.find_all("a", href=True) if "dice.fm" in a["href"]), None)
        if codigo:
            return Lista(DICE_CODIGO, fecha, url=dice, codigo=codigo.group(1))
    return None
