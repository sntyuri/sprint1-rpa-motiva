"""Captura de solicitações em planilhas (Excel ou CSV) deixadas na pasta entrada/."""
import hashlib
import logging
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config, pipeline

log = logging.getLogger("motiva_rpa")

EXTENSOES = {".csv", ".xlsx", ".xls"}
# Nomes de coluna aceitos para o texto da solicitação (comparados sem acento e em minúsculas).
COLUNAS_TEXTO = ["relato", "descricao", "mensagem", "texto", "ocorrencia", "solicitacao", "observacao"]


def _normalizar(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    return sem_acento.strip().lower().replace(" ", "_")


def ler_planilha(caminho: Path) -> pd.DataFrame:
    if caminho.suffix.lower() == ".csv":
        # Planilhas exportadas no Brasil costumam vir com ponto e vírgula; o pandas descobre sozinho.
        df = pd.read_csv(caminho, sep=None, engine="python", dtype=str, encoding="utf-8-sig")
    else:
        df = pd.read_excel(caminho, dtype=str)
    return df.fillna("")


def coluna_do_texto(df: pd.DataFrame) -> str:
    normalizadas = {_normalizar(c): c for c in df.columns}
    for candidata in COLUNAS_TEXTO:
        for norm, original in normalizadas.items():
            if norm.startswith(candidata):
                return original
    raise ValueError(f"Nenhuma coluna de texto encontrada. Use uma destas: {', '.join(COLUNAS_TEXTO)}")


def processar_arquivo(caminho: Path, origem: str = "arquivo") -> list[dict]:
    df = ler_planilha(caminho)
    col_texto = coluna_do_texto(df)
    resultados = []
    for i, linha in df.iterrows():
        texto = linha[col_texto]
        # As outras colunas (data, nome, telefone, km...) seguem como contexto para a IA.
        contexto = "\n".join(f"{c}: {linha[c]}" for c in df.columns if c != col_texto and str(linha[c]).strip())
        # A referência usa o conteúdo da linha: reenviar a mesma planilha não duplica registros.
        impressao = hashlib.sha1(f"{texto}|{contexto}".encode()).hexdigest()[:12]
        r = pipeline.processar(texto, canal=origem, origem_ref=f"{origem}:{caminho.name}:{impressao}",
                               assunto=f"{caminho.name}, linha {i + 2}", contexto=contexto)
        if r:
            resultados.append(r)
    return resultados


def varrer_pasta() -> list[dict]:
    """Processa e arquiva toda planilha que estiver em entrada/."""
    config.garantir_pastas()
    resultados = []
    for arquivo in sorted(config.PASTA_ENTRADA.iterdir()):
        if not arquivo.is_file() or arquivo.suffix.lower() not in EXTENSOES or arquivo.name.startswith("~$"):
            continue
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            log.info("Planilha encontrada: %s", arquivo.name)
            resultados += processar_arquivo(arquivo)
            shutil.move(arquivo, config.PASTA_ENTRADA / "processados" / f"{carimbo}_{arquivo.name}")
        except Exception as e:
            log.error("Não consegui ler %s: %s", arquivo.name, e)
            shutil.move(arquivo, config.PASTA_ENTRADA / "com_erro" / f"{carimbo}_{arquivo.name}")
    return resultados
