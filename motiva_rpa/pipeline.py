"""Caminho único de toda solicitação, venha ela de e-mail, planilha ou voz:
interpretar com IA -> registrar -> encaminhar."""
import logging

from . import encaminhamento, ia, registro

log = logging.getLogger("motiva_rpa")


def processar(texto: str, canal: str, origem_ref: str | None = None, remetente: str | None = None,
              assunto: str | None = None, contexto: str = "") -> dict | None:
    """Processa uma solicitação. Devolve None se ela já tinha sido processada antes."""
    if origem_ref and registro.ja_processado(origem_ref):
        return None
    if not texto or not texto.strip():
        log.warning("Solicitação vazia ignorada (%s)", origem_ref)
        return None

    entrada = {"texto": texto, "canal": canal, "origem_ref": origem_ref, "remetente": remetente, "assunto": assunto}
    try:
        dados = ia.classificar(texto, canal, contexto or (f"Assunto: {assunto}" if assunto else ""))
    except ia.ErroIA as e:
        # Sem IA a solicitação não se perde: fica registrada para alguém triar à mão.
        protocolo = registro.salvar(entrada, None, erro=str(e))
        log.error("%s: IA indisponível (%s). Registrada para triagem manual.", protocolo, e)
        return {"protocolo": protocolo, "status": "aguardando_triagem", "erro": str(e)}

    protocolo = registro.salvar(entrada, dados)
    resultado = encaminhamento.encaminhar(protocolo, dados, entrada)
    log.info("%s | %s/%s | %s -> %s", protocolo, dados["categoria"], dados["severidade"],
             resultado["status"], ", ".join(resultado["equipes"]))
    return {"protocolo": protocolo, **resultado, "classificacao": dados}
