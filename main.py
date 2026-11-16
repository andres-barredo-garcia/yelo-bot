"""Bot de listas de Yelo.

Uso:
  python main.py chat-id         -> muestra tu chat id de Telegram (antes manda /start a tu bot)
  python main.py test-telegram   -> envía un mensaje de prueba
  python main.py revisar         -> revisa el correo una vez y procesa listas nuevas
  python main.py revisar --prueba  -> reprocesa los correos de los últimos días, solo avisa
                                      (no abre Xceed ni etiqueta los correos)
  python main.py run             -> bucle infinito (para dejarlo corriendo)
  python main.py probar-html ARCHIVO.html -> clasifica un correo guardado, sin red
"""
import sys
import time
import traceback
from pathlib import Path

from bot import clasificador, config, gmail_reader, telegram
from bot.clasificador import DICE_CODIGO, DICE_LINK, XCEED
from bot.telegram import esc


def procesar(correo: gmail_reader.Correo, prueba: bool) -> bool:
    lista = clasificador.clasificar(correo.html, correo.texto)
    if lista is None:
        return False
    titulo = f"Lista Yelo {lista.fecha or ''}".strip()
    asunto = esc(correo.asunto)

    if lista.tipo == XCEED:
        telegram.enviar(
            f"🟦 <b>{titulo} (Xceed)</b>\n{asunto}\n\nEl bot lo está intentando; si quieres asegurar, entra tú ya.",
            ("Abrir en Xceed", lista.url),
        )
        if not prueba:
            from bot import xceed
            r = xceed.explorar(lista.url)
            if r["hay_plazas"] is False:
                telegram.enviar(f"❌ <b>{titulo}</b>: Xceed dice que no hay plazas.")
            else:
                estado = "llegó a «Mis datos» (sin enviar nada)" if r["llego_a_datos"] else "no llegó a «Mis datos»"
                extra = f"\nError: {esc(r['error'])}" if r["error"] else ""
                telegram.enviar(f"🔎 Exploración Xceed: cantidad +{r['cantidad']}, {estado}.{extra}")
                for captura in r["capturas"]:
                    telegram.enviar_foto(str(captura), f"Xceed · {captura.stem}")
    elif lista.tipo == DICE_LINK:
        telegram.enviar(f"🎟️ <b>{titulo} (Dice)</b>\n{asunto}\n\nEntra ya 👇", ("Abrir en Dice", lista.url))
    elif lista.tipo == DICE_CODIGO:
        boton = ("Abrir Dice", lista.url) if lista.url else None
        telegram.enviar(f"🎟️ <b>{titulo} (código Dice)</b>\n{asunto}\n\nCódigo: <code>{esc(lista.codigo)}</code>",
                        boton)
    else:
        boton = ("Abrir link", lista.url) if lista.url else None
        telegram.enviar(f"❓ <b>{titulo}</b>: hay lista pero no reconozco el tipo.\n{asunto}", boton)
    return True


def revisar(prueba: bool = False) -> None:
    # Los logs de GitHub Actions son públicos: aquí solo se imprimen contadores.
    correos = gmail_reader.correos_yelo(incluir_procesados=prueba)
    procesados, listas = [], 0
    for correo in correos:
        try:
            listas += procesar(correo, prueba)
        except Exception as e:
            print(f"Error procesando un correo: {type(e).__name__}")
            try:
                telegram.enviar(f"⚠️ Error procesando: {esc(correo.asunto)}\n{esc(type(e).__name__)}: {esc(str(e))[:300]}")
            except Exception:
                pass
        procesados.append(correo.uid)
    if not prueba:
        gmail_reader.marcar_procesado(procesados)
    print(f"Correos nuevos: {len(correos)} · listas encontradas: {listas}")


def main(argv: list[str]) -> None:
    cmd = argv[1] if len(argv) > 1 else "revisar"
    if cmd == "chat-id":
        chats = telegram.obtener_chat_ids()
        if not chats:
            print("No hay mensajes. Abre tu bot en Telegram, pulsa Iniciar (/start) y repite.")
        for cid, nombre in chats:
            print(f"TELEGRAM_CHAT_ID={cid}   ({nombre})")
    elif cmd == "test-telegram":
        telegram.enviar("✅ <b>Bot de Yelo conectado.</b> Aquí te llegarán los avisos de lista.")
        print("Enviado.")
    elif cmd == "revisar":
        revisar(prueba="--prueba" in argv)
    elif cmd == "run":
        print(f"Revisando cada {config.INTERVALO_SEGUNDOS}s. Ctrl+C para parar.")
        while True:
            try:
                revisar()
            except Exception:
                traceback.print_exc()
            time.sleep(config.INTERVALO_SEGUNDOS)
    elif cmd == "probar-html":
        html = Path(argv[2]).read_text(encoding="utf-8", errors="replace")
        print(clasificador.clasificar(html, resolver_links="--sin-red" not in argv))
    else:
        print(__doc__)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main(sys.argv)
