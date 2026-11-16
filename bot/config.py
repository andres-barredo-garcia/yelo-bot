import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

LOGS_DIR = ROOT / "logs"


def get(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise SystemExit(f"Falta la variable {name} en el archivo .env")
    return value or ""


GMAIL_USER = get("GMAIL_USER")
GMAIL_APP_PASSWORD = get("GMAIL_APP_PASSWORD")
YELO_FROM = get("YELO_FROM", "yelo")
DIAS_ATRAS = int(get("DIAS_ATRAS", "7"))

TELEGRAM_BOT_TOKEN = get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get("TELEGRAM_CHAT_ID")

TITULAR_NOMBRE = get("TITULAR_NOMBRE", "")
TITULAR_APELLIDOS = get("TITULAR_APELLIDOS", "")
XCEED_ENTRADAS = int(get("XCEED_ENTRADAS", "6"))

INTERVALO_SEGUNDOS = int(get("INTERVALO_SEGUNDOS", "60"))
