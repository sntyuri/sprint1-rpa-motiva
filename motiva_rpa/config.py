"""Caminhos e configurações lidas do .env."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

PASTA_ENTRADA = RAIZ / "entrada"
PASTA_SAIDA = RAIZ / "saida"
PASTA_DADOS = RAIZ / "dados"
BANCO = PASTA_DADOS / "ocorrencias.db"
ARQ_CAIXA_EMAIL = RAIZ / "config" / "caixa_email.json"
ARQ_RESPONSAVEIS = RAIZ / "config" / "responsaveis.json"

MODELO_IA = os.getenv("MODELO_IA", "claude-opus-5-5")
INTERVALO_SEGUNDOS = int(os.getenv("INTERVALO_SEGUNDOS", "20"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORTA = int(os.getenv("SMTP_PORTA", "587"))
SMTP_USUARIO = os.getenv("SMTP_USUARIO", "")
SMTP_SENHA = os.getenv("SMTP_SENHA", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")


def responsaveis() -> dict:
    return json.loads(ARQ_RESPONSAVEIS.read_text(encoding="utf-8"))


def garantir_pastas() -> None:
    for pasta in (PASTA_ENTRADA, PASTA_SAIDA, PASTA_DADOS,
                  PASTA_ENTRADA / "processados", PASTA_ENTRADA / "com_erro"):
        pasta.mkdir(parents=True, exist_ok=True)
