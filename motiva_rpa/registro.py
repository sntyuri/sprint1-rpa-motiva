"""Registro estruturado das ocorrências em SQLite, com exportação para Excel."""
import json
import sqlite3
from datetime import datetime

import pandas as pd

from . import config

_TABELAS = """
CREATE TABLE IF NOT EXISTS ocorrencias (
    protocolo TEXT PRIMARY KEY,
    recebido_em TEXT NOT NULL,
    canal TEXT NOT NULL,
    origem_ref TEXT UNIQUE,
    remetente TEXT,
    assunto TEXT,
    texto_original TEXT NOT NULL,
    categoria TEXT,
    subtipo TEXT,
    severidade TEXT,
    risco_a_vida INTEGER,
    resumo TEXT,
    rodovia TEXT,
    km REAL,
    sentido TEXT,
    referencia TEXT,
    veiculos_envolvidos INTEGER,
    ha_vitimas TEXT,
    qtd_vitimas INTEGER,
    pista_bloqueada TEXT,
    solicitante_nome TEXT,
    solicitante_telefone TEXT,
    solicitante_email TEXT,
    informacoes_faltantes TEXT,
    confianca REAL,
    justificativa TEXT,
    equipes TEXT,
    prazo_atendimento TEXT,
    status TEXT NOT NULL,
    modelo_ia TEXT,
    erro TEXT
);
CREATE TABLE IF NOT EXISTS encaminhamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo TEXT NOT NULL REFERENCES ocorrencias(protocolo),
    equipe TEXT NOT NULL,
    meio TEXT NOT NULL,
    destino TEXT,
    enviado_em TEXT NOT NULL,
    sucesso INTEGER NOT NULL,
    detalhe TEXT
);
"""


def conectar() -> sqlite3.Connection:
    config.garantir_pastas()
    con = sqlite3.connect(config.BANCO)
    con.row_factory = sqlite3.Row
    con.executescript(_TABELAS)
    return con


def ja_processado(origem_ref: str) -> bool:
    with conectar() as con:
        return con.execute("SELECT 1 FROM ocorrencias WHERE origem_ref = ?", (origem_ref,)).fetchone() is not None


def novo_protocolo(con: sqlite3.Connection) -> str:
    hoje = datetime.now().strftime("%Y%m%d")
    n = con.execute("SELECT COUNT(*) FROM ocorrencias WHERE protocolo LIKE ?", (f"OC-{hoje}-%",)).fetchone()[0]
    return f"OC-{hoje}-{n + 1:04d}"


def salvar(entrada: dict, ia: dict | None, erro: str | None = None) -> str:
    """Grava a ocorrência e devolve o protocolo. `ia` é None quando a IA falhou."""
    with conectar() as con:
        protocolo = novo_protocolo(con)
        linha = {
            "protocolo": protocolo,
            "recebido_em": datetime.now().isoformat(timespec="seconds"),
            "canal": entrada["canal"],
            "origem_ref": entrada.get("origem_ref"),
            "remetente": entrada.get("remetente"),
            "assunto": entrada.get("assunto"),
            "texto_original": entrada["texto"],
            "status": "aguardando_triagem" if ia is None else "classificada",
            "erro": erro,
        }
        if ia:
            local, vitimas, solicitante = ia["local"], ia["vitimas"], ia["solicitante"]
            linha.update({
                "categoria": ia["categoria"], "subtipo": ia["subtipo"], "severidade": ia["severidade"],
                "risco_a_vida": int(ia["risco_a_vida"]), "resumo": ia["resumo"],
                "rodovia": local["rodovia"], "km": local["km"], "sentido": local["sentido"],
                "referencia": local["referencia"], "veiculos_envolvidos": ia["veiculos_envolvidos"],
                "ha_vitimas": vitimas["ha_vitimas"], "qtd_vitimas": vitimas["quantidade"],
                "pista_bloqueada": ia["pista_bloqueada"],
                "solicitante_nome": solicitante["nome"], "solicitante_telefone": solicitante["telefone"],
                "solicitante_email": solicitante["email"] or entrada.get("remetente"),
                "informacoes_faltantes": json.dumps(ia["informacoes_faltantes"], ensure_ascii=False),
                "confianca": ia["confianca"], "justificativa": ia["justificativa"],
                "modelo_ia": ia.get("_modelo"),
            })
        colunas = ", ".join(linha)
        con.execute(f"INSERT INTO ocorrencias ({colunas}) VALUES ({', '.join('?' * len(linha))})",
                    list(linha.values()))
    return protocolo


def atualizar_encaminhamento(protocolo: str, equipes: list[str], status: str, prazo: str | None) -> None:
    with conectar() as con:
        con.execute("UPDATE ocorrencias SET equipes = ?, status = ?, prazo_atendimento = ? WHERE protocolo = ?",
                    (json.dumps(equipes), status, prazo, protocolo))


def registrar_envio(protocolo: str, equipe: str, meio: str, destino: str, sucesso: bool, detalhe: str = "") -> None:
    with conectar() as con:
        con.execute(
            "INSERT INTO encaminhamentos (protocolo, equipe, meio, destino, enviado_em, sucesso, detalhe) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (protocolo, equipe, meio, destino, datetime.now().isoformat(timespec="seconds"), int(sucesso), detalhe))


def buscar(protocolo: str) -> dict | None:
    with conectar() as con:
        linha = con.execute("SELECT * FROM ocorrencias WHERE protocolo = ?", (protocolo.strip().upper(),)).fetchone()
    return dict(linha) if linha else None


def listar(limite: int = 20) -> list[dict]:
    with conectar() as con:
        return [dict(l) for l in con.execute(
            "SELECT * FROM ocorrencias ORDER BY recebido_em DESC, protocolo DESC LIMIT ?", (limite,))]


def exportar_excel() -> str:
    """Gera saida/ocorrencias.xlsx com uma aba de ocorrências e outra de encaminhamentos."""
    with conectar() as con:
        ocorrencias = pd.read_sql("SELECT * FROM ocorrencias ORDER BY recebido_em", con)
        envios = pd.read_sql("SELECT * FROM encaminhamentos ORDER BY id", con)
    destino = config.PASTA_SAIDA / "ocorrencias.xlsx"
    with pd.ExcelWriter(destino) as planilha:
        ocorrencias.to_excel(planilha, sheet_name="ocorrencias", index=False)
        envios.to_excel(planilha, sheet_name="encaminhamentos", index=False)
    return str(destino)
