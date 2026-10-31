"""Decide quem atende cada ocorrência e entrega o aviso para essas equipes.

A decisão de quem atende é uma regra fixa sobre o que a IA extraiu, e não da IA.
Assim a operação consegue auditar e mudar o roteamento sem mexer em prompt.
"""
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

import requests

from . import config, registro

def definir_equipes(ia: dict) -> list[str]:
    cat = ia["categoria"]
    bloqueada = ia["pista_bloqueada"] in ("total", "parcial")
    grave = ia["severidade"] in ("alta", "critica")

    if cat == "acidente":
        equipes = ["cco", "guincho"]
        if ia["risco_a_vida"] or ia["vitimas"]["ha_vitimas"] != "nao":
            equipes.insert(1, "resgate")
    elif cat == "veiculo_avariado":
        equipes = ["guincho"] + (["cco"] if bloqueada or grave else [])
    elif cat in ("objeto_na_pista", "animal_na_pista"):
        equipes = ["inspecao"] + (["cco"] if grave else [])
    elif cat == "pedestre_na_pista":
        equipes = ["inspecao", "cco"]
    elif cat == "problema_na_via":
        equipes = ["conservacao"] + (["cco"] if grave else [])
    elif cat == "evento_ambiental":
        equipes = ["cco"]
    elif cat == "atendimento_usuario":
        equipes = ["ouvidoria"]
    else:
        equipes = ["triagem"]

    # Resgate é atendimento a pessoas: entra quando há vítima, não só porque a situação é perigosa
    # (um animal na pista é perigoso, mas quem resolve é a inspeção).
    pessoas_em_risco = ia["vitimas"]["ha_vitimas"] == "sim" or (
        ia["risco_a_vida"] and cat in ("acidente", "pedestre_na_pista", "evento_ambiental"))
    if pessoas_em_risco and "resgate" not in equipes:
        equipes.append("resgate")
    return equipes


def precisa_triagem(ia: dict, confianca_minima: float) -> bool:
    """Casos em que um humano confirma antes de a equipe agir (princípio Human-in-the-Loop)."""
    return ia["confianca"] < confianca_minima or ia["categoria"] == "nao_e_ocorrencia"


def montar_aviso(protocolo: str, ia: dict, entrada: dict, equipe_nome: str, prazo: str, em_triagem: bool) -> tuple[str, str]:
    local = ia["local"]
    onde = ", ".join(str(x) for x in [local["rodovia"], f"km {local['km']}" if local["km"] is not None else None,
                                      f"sentido {local['sentido']}" if local["sentido"] else None,
                                      local["referencia"]] if x) or "local não informado"
    assunto = f"[{ia['severidade'].upper()}] {protocolo} · {ia['categoria'].replace('_', ' ')} · {onde}"
    linhas = [
        f"Equipe: {equipe_nome}",
        f"Protocolo: {protocolo}",
        f"Atender até: {prazo}",
        "",
        f"Resumo: {ia['resumo']}",
        f"Local: {onde}",
        f"Vítimas: {ia['vitimas']['ha_vitimas']}" + (f" ({ia['vitimas']['quantidade']})" if ia["vitimas"]["quantidade"] else ""),
        f"Pista bloqueada: {ia['pista_bloqueada']}",
        f"Contato: {ia['solicitante']['nome'] or '-'} {ia['solicitante']['telefone'] or ''}".rstrip(),
    ]
    if ia["informacoes_faltantes"]:
        linhas.append("Confirmar com o solicitante: " + "; ".join(ia["informacoes_faltantes"]))
    if em_triagem:
        linhas += ["", f"ATENÇÃO: a IA teve baixa confiança ({ia['confianca']:.0%}). Confirme a classificação antes de despachar."]
    linhas += ["", f"Classificação automática (confiança {ia['confianca']:.0%}): {ia['justificativa']}",
               "", f"Mensagem original ({entrada['canal']}):", entrada["texto"].strip()]
    return assunto, "\n".join(linhas)


def _salvar_na_caixa_de_saida(equipe: str, protocolo: str, msg: EmailMessage) -> str:
    pasta = config.PASTA_SAIDA / "encaminhamentos" / equipe
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"{protocolo}.eml"
    arquivo.write_bytes(bytes(msg))
    return str(arquivo)


def _enviar_smtp(msg: EmailMessage) -> None:
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORTA, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(config.SMTP_USUARIO, config.SMTP_SENHA)
        smtp.send_message(msg)


def _enviar_webhook(assunto: str, corpo: str) -> None:
    texto = f"**{assunto}**\n```\n{corpo[:1700]}\n```"
    # "content" é o campo do Discord; "text" é o do Slack e do Teams.
    r = requests.post(config.WEBHOOK_URL, json={"content": texto, "text": texto}, timeout=15)
    r.raise_for_status()


def encaminhar(protocolo: str, ia: dict, entrada: dict) -> dict:
    regras = config.responsaveis()
    em_triagem = precisa_triagem(ia, regras["confianca_minima"])
    equipes = definir_equipes(ia)
    if em_triagem and "triagem" not in equipes:
        equipes.insert(0, "triagem")

    severidade = ia["severidade"]
    prazos = [regras["equipes"][e]["prazo_minutos"][severidade] for e in equipes]
    prazo = (datetime.now() + timedelta(minutes=min(prazos))).strftime("%d/%m/%Y %H:%M")

    for equipe in equipes:
        dados = regras["equipes"][equipe]
        assunto, corpo = montar_aviso(protocolo, ia, entrada, dados["nome"], prazo, em_triagem)
        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = config.SMTP_USUARIO or "robo-triagem@motiva.local"
        msg["To"] = dados["email"] or f"{equipe}@motiva.local"
        msg.set_content(corpo)

        caminho = _salvar_na_caixa_de_saida(equipe, protocolo, msg)
        registro.registrar_envio(protocolo, equipe, "caixa_de_saida", caminho, True)

        if config.SMTP_HOST and dados["email"]:
            try:
                _enviar_smtp(msg)
                registro.registrar_envio(protocolo, equipe, "email", dados["email"], True)
            except Exception as e:  # um e-mail que falha não pode travar os outros avisos
                registro.registrar_envio(protocolo, equipe, "email", dados["email"], False, str(e))
        if config.WEBHOOK_URL:
            try:
                _enviar_webhook(assunto, corpo)
                registro.registrar_envio(protocolo, equipe, "webhook", "canal", True)
            except Exception as e:
                registro.registrar_envio(protocolo, equipe, "webhook", "canal", False, str(e))

    status = "aguardando_triagem" if em_triagem else "encaminhada"
    registro.atualizar_encaminhamento(protocolo, equipes, status, prazo)
    return {"equipes": equipes, "status": status, "prazo": prazo}
