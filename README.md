# Bot de listas de Yelo

Revisa un Gmail cada 5 minutos (GitHub Actions). Cuando llega un correo de Yelo con **Lista GRATIS**:

| Tipo | Qué hace |
|---|---|
| Link Xceed | Avisa al momento con botón + explora la reserva (sin enviar nada, de momento) |
| Link Dice | Aviso con botón "Abrir en Dice" |
| Código Dice | Aviso con el código para copiar |

Los correos ya tratados se marcan con la etiqueta de Gmail `yelo-bot-procesado` (no se marcan como leídos).

## Configuración en GitHub

En el repo: **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Valor |
|---|---|
| `GMAIL_USER` | tu dirección de Gmail |
| `GMAIL_APP_PASSWORD` | contraseña de aplicación de Google (https://myaccount.google.com/apppasswords) |
| `TELEGRAM_BOT_TOKEN` | token de @BotFather |
| `TELEGRAM_CHAT_ID` | tu chat id (`python main.py chat-id`) |
| `TITULAR_NOMBRE` / `TITULAR_APELLIDOS` | nombre del titular de las entradas |

Opcional, en la pestaña **Variables**: `YELO_FROM` (texto del remitente, por defecto `yelo`) y
`XCEED_ENTRADAS` (por defecto `6`).

Prueba: pestaña **Actions → Yelo listas → Run workflow**.

## Uso local

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
copy .env.example .env   # y rellénalo
.venv\Scripts\python main.py test-telegram
.venv\Scripts\python main.py revisar --prueba
```

## Pendiente
- **Xceed automático**: con la próxima lista abierta el bot manda por Telegram capturas de la
  pantalla «Mis datos». Con eso se completa el relleno y envío de las entradas.
