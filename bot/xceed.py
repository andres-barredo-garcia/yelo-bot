"""Xceed: modo exploración.

Todavía no conocemos los campos de "Mis datos" (la lista que vimos estaba agotada),
así que de momento este módulo:
  1. Abre el link, rechaza cookies y mira si hay plazas.
  2. Intenta subir la cantidad hasta XCEED_ENTRADAS y pulsar CONTINUAR.
  3. Guarda captura + HTML de cada paso en logs/ y SE PARA antes de enviar nada.
Con lo que guarde la próxima lista abierta completamos el envío automático.
"""
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import config

_SIN_PLAZAS = re.compile(r"no hay ofertas disponibles|no offers available|agotad|sold out", re.I)
_MAS = re.compile(r"^\+$|increase|increment|add|añadir|sumar", re.I)


def _instalar_chromium_si_hace_falta() -> None:
    # En GitHub Actions el navegador solo se descarga cuando llega una lista de Xceed,
    # así el resto de ejecuciones duran unos segundos.
    if os.getenv("GITHUB_ACTIONS") == "true":
        subprocess.run([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],
                       check=True, stdout=subprocess.DEVNULL)


def explorar(url: str) -> dict:
    from playwright.sync_api import sync_playwright

    _instalar_chromium_si_hace_falta()

    carpeta = config.LOGS_DIR / f"xceed-{datetime.now():%Y%m%d-%H%M%S}"
    carpeta.mkdir(parents=True, exist_ok=True)
    capturas: list[Path] = []

    def guardar(page, nombre: str) -> None:
        ruta = carpeta / f"{len(capturas) + 1:02d}-{nombre}.png"
        page.screenshot(path=str(ruta), full_page=True)
        (carpeta / f"{len(capturas) + 1:02d}-{nombre}.html").write_text(page.content(), encoding="utf-8")
        capturas.append(ruta)

    resultado = {"hay_plazas": None, "cantidad": 0, "llego_a_datos": False,
                 "carpeta": str(carpeta), "capturas": capturas, "error": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="es-ES", viewport={"width": 430, "height": 900})
        try:
            page.goto(url, wait_until="networkidle", timeout=45_000)
            try:
                page.get_by_role("button", name=re.compile("rechazarlas todas|reject all", re.I)).click(timeout=4_000)
            except Exception:
                pass
            guardar(page, "inicio")

            texto = page.inner_text("body")
            resultado["hay_plazas"] = not _SIN_PLAZAS.search(texto)
            if not resultado["hay_plazas"]:
                return resultado

            # Subir cantidad pulsando el botón "+"
            for _ in range(config.XCEED_ENTRADAS):
                botones = [b for b in page.get_by_role("button").all()
                           if _MAS.search((b.get_attribute("aria-label") or "") + " " + (b.inner_text() or "").strip())]
                if not botones or not botones[0].is_enabled():
                    break
                botones[0].click()
                resultado["cantidad"] += 1
                page.wait_for_timeout(300)
            guardar(page, "cantidad")

            page.get_by_role("button", name=re.compile("continuar|continue", re.I)).click(timeout=8_000)
            page.wait_for_load_state("networkidle", timeout=20_000)
            guardar(page, "mis-datos")
            resultado["llego_a_datos"] = True
            # STOP: no se rellena ni se envía nada hasta conocer el formulario.
        except Exception as e:  # noqa: BLE001
            resultado["error"] = f"{type(e).__name__}: {e}"
            try:
                guardar(page, "error")
            except Exception:
                pass
        finally:
            browser.close()
    return resultado
