"""Captura de solicitações por e-mail usando uma caixa temporária do Guerrilla Mail.

O Guerrilla Mail tem uma API gratuita e sem cadastro: escolhemos um nome de caixa,
divulgamos o endereço e o robô consulta as mensagens novas. Planilhas anexadas
seguem para a captura por arquivo.

(Começamos com o mail.tm, mas o domínio que ele entregou não tinha registro MX no DNS
e o Gmail devolvia as mensagens.)
"""
import json
import logging
import re
import secrets
from html import unescape

import requests

from . import captura_arquivo, config, pipeline, registro

log = logging.getLogger("motiva_rpa")
API = "https://api.guerrillamail.com/ajax.php"
REMETENTES_IGNORADOS = ("no-reply@guerrillamail.com",)  # mensagem de boas-vindas do serviço


class CaixaTemporaria:
    def __init__(self, usuario: str, vistos: list[str] | None = None):
        self.usuario = usuario
        self.vistos = set(vistos or [])
        self.endereco = None
        self._sessao = requests.Session()
        self._token = None

    @classmethod
    def criar(cls, prefixo: str = "ocorrencias-motiva") -> "CaixaTemporaria":
        caixa = cls(f"{prefixo}-{secrets.token_hex(3)}")
        caixa.conectar()
        caixa.salvar()
        return caixa

    @classmethod
    def carregar(cls) -> "CaixaTemporaria | None":
        if not config.ARQ_CAIXA_EMAIL.exists():
            return None
        dados = json.loads(config.ARQ_CAIXA_EMAIL.read_text())
        return cls(dados["usuario"], dados.get("vistos"))

    def salvar(self) -> None:
        config.ARQ_CAIXA_EMAIL.write_text(json.dumps(
            {"usuario": self.usuario, "endereco": self.endereco, "vistos": sorted(self.vistos)}, indent=2))

    def _chamar(self, funcao: str, **params) -> dict:
        r = self._sessao.get(API, params={"f": funcao, "lang": "en", "sid_token": self._token, **params}, timeout=30)
        r.raise_for_status()
        dados = r.json()
        self._token = dados.get("sid_token", self._token)
        return dados

    def conectar(self) -> None:
        """Abre uma sessão e reivindica sempre o mesmo nome de caixa."""
        self._token = self._chamar("get_email_address")["sid_token"]
        self.endereco = self._chamar("set_email_user", email_user=self.usuario)["email_addr"]

    def mensagens(self) -> list[dict]:
        return self._chamar("get_email_list", offset=0).get("list", [])

    def ler(self, id_msg) -> dict:
        return self._chamar("fetch_email", email_id=id_msg)

    def baixar_anexo(self, id_msg, parte) -> bytes:
        r = self._sessao.get("https://www.guerrillamail.com/inbox", timeout=30, params={
            "get_att": "", "lang": "en", "email_id": id_msg, "part_id": parte, "sid_token": self._token})
        r.raise_for_status()
        return r.content


def _texto_do_email(corpo: str) -> str:
    """O corpo vem em HTML; viramos texto simples para a IA."""
    corpo = re.sub(r"<br\s*/?>|</p>|</div>", "\n", corpo, flags=re.I)
    texto = unescape(re.sub(r"<[^>]+>", " ", corpo))
    return re.sub(r"[ \t]+", " ", texto).strip()


def _sem_resposta_citada(texto: str) -> str:
    """Corta o histórico citado ("Em ... escreveu:") para a IA ler só a mensagem nova."""
    partes = re.split(r"\n\s*(?:Em .+ escreveu:|On .+ wrote:|-{2,} ?Mensagem original)", texto, maxsplit=1)
    return partes[0].strip()


def verificar_caixa() -> list[dict]:
    caixa = CaixaTemporaria.carregar()
    if caixa is None:
        log.warning("Nenhuma caixa de e-mail configurada. Rode: python -m motiva_rpa criar-caixa")
        return []
    caixa.conectar()
    resultados = []
    for resumo in caixa.mensagens():
        id_msg = str(resumo["mail_id"])
        if id_msg in caixa.vistos or resumo["mail_from"] in REMETENTES_IGNORADOS:
            continue
        msg = caixa.ler(id_msg)
        remetente = msg["mail_from"]
        log.info("E-mail recebido de %s: %s", remetente, msg.get("mail_subject") or "(sem assunto)")

        trouxe_planilha = False
        for anexo in msg.get("att_info") or []:
            nome = anexo.get("f", "")
            if any(nome.lower().endswith(ext) for ext in captura_arquivo.EXTENSOES):
                destino = config.PASTA_ENTRADA / f"email_{id_msg}_{nome}"
                destino.write_bytes(caixa.baixar_anexo(id_msg, anexo["p"]))
                log.info("Anexo %s salvo em entrada/ para a captura por arquivo", nome)
                trouxe_planilha = True

        texto = _sem_resposta_citada(_texto_do_email(msg.get("mail_body", "")))
        # "Segue a planilha" não é uma ocorrência: nesse caso só o anexo é processado.
        if not (trouxe_planilha and len(texto) < 200):
            r = pipeline.processar(texto, canal="email", origem_ref=f"email:{caixa.usuario}:{id_msg}",
                                   remetente=remetente, assunto=msg.get("mail_subject"))
            if r:
                resultados.append(r)
        caixa.vistos.add(id_msg)
        caixa.salvar()
    return resultados
