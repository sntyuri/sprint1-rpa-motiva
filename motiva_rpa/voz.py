"""Funções que o agente de voz vai chamar nas próximas sprints.

O agente de voz transcreve a ligação e chama `registrar_ocorrencia_por_voz`. A resposta
traz o protocolo, o que já foi feito e uma frase pronta para ele falar ao usuário,
além das perguntas que ainda faltam fazer.

`FERRAMENTAS_VOZ` descreve as funções no formato de tool use da API do Claude, para o
agente decidir sozinho quando chamar cada uma; `executar_ferramenta` faz a ponte.
"""
import json

from . import pipeline, registro

_NOMES_EQUIPE = {
    "cco": "o Centro de Controle", "resgate": "o resgate", "guincho": "o guincho",
    "inspecao": "a inspeção de tráfego", "conservacao": "a equipe de conservação",
    "ouvidoria": "a ouvidoria", "triagem": "um supervisor",
}


def _juntar(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def _fala(protocolo: str, resultado: dict) -> str:
    dados = resultado["classificacao"]
    equipes = _juntar([_NOMES_EQUIPE[e] for e in resultado["equipes"]])
    numero_do_dia = int(protocolo.split("-")[-1])  # "OC-20261030-0009" é falado como "número 9 de hoje"
    if dados["risco_a_vida"]:
        inicio = f"Já acionei {equipes}. Se puder, fique em local seguro, longe da pista."
    elif resultado["status"] == "aguardando_triagem":
        inicio = f"Registrei sua solicitação e {equipes} vai confirmar os detalhes."
    else:
        inicio = f"Registrei e já avisei {equipes}."
    return f"{inicio} Sua ocorrência é a de número {numero_do_dia} de hoje."


def registrar_ocorrencia_por_voz(transcricao: str, telefone: str | None = None,
                                 local_informado: str | None = None) -> dict:
    """Registra e encaminha uma ocorrência a partir da transcrição de uma ligação."""
    contexto = "\n".join(x for x in [f"Telefone de quem ligou: {telefone}" if telefone else "",
                                     f"Local informado pelo sistema: {local_informado}" if local_informado else ""] if x)
    resultado = pipeline.processar(transcricao, canal="voz", contexto=contexto)
    if resultado is None:
        return {"ok": False, "fala_sugerida": "Não entendi a solicitação. Pode repetir o que aconteceu?"}
    if "erro" in resultado:
        return {"ok": True, "protocolo": resultado["protocolo"], "status": resultado["status"],
                "perguntas_pendentes": [],
                "fala_sugerida": "Registrei sua ligação e um atendente vai dar continuidade em instantes."}
    dados = resultado["classificacao"]
    return {
        "ok": True,
        "protocolo": resultado["protocolo"],
        "categoria": dados["categoria"],
        "severidade": dados["severidade"],
        "equipes_acionadas": resultado["equipes"],
        "status": resultado["status"],
        "atender_ate": resultado["prazo"],
        "perguntas_pendentes": dados["informacoes_faltantes"],
        "fala_sugerida": _fala(resultado["protocolo"], resultado),
    }


def consultar_ocorrencia(protocolo: str) -> dict:
    """Situação atual de uma ocorrência, para o usuário que liga perguntando."""
    oc = registro.buscar(protocolo)
    if oc is None:
        return {"ok": False, "fala_sugerida": "Não encontrei esse protocolo. Pode confirmar os números?"}
    equipes = json.loads(oc["equipes"] or "[]")
    situacao = {"encaminhada": "já foi encaminhada", "aguardando_triagem": "está com um supervisor para confirmação",
                "classificada": "foi registrada"}.get(oc["status"], oc["status"])
    return {
        "ok": True, "protocolo": oc["protocolo"], "status": oc["status"], "categoria": oc["categoria"],
        "resumo": oc["resumo"], "equipes": equipes, "atender_ate": oc["prazo_atendimento"],
        "fala_sugerida": f"A ocorrência {situacao}"
                         + (f" para {_juntar([_NOMES_EQUIPE[e] for e in equipes])}" if equipes else "")
                         + (f", com atendimento previsto até {oc['prazo_atendimento'][-5:]}." if oc["prazo_atendimento"] else "."),
    }


FERRAMENTAS_VOZ = [
    {
        "name": "registrar_ocorrencia",
        "description": ("Registra uma ocorrência na rodovia relatada por telefone e aciona as equipes responsáveis. "
                        "Chame assim que a pessoa descrever o que aconteceu, mesmo sem todos os detalhes; "
                        "depois use perguntas_pendentes para completar a conversa."),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "transcricao": {"type": "string", "description": "O que a pessoa contou, com as palavras dela."},
                "telefone": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Número de quem ligou, se conhecido."},
                "local_informado": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Rodovia, km ou referência, se a pessoa disse."},
            },
            "required": ["transcricao", "telefone", "local_informado"],
            "additionalProperties": False,
        },
    },
    {
        "name": "consultar_ocorrencia",
        "description": "Consulta a situação de uma ocorrência já registrada, pelo número do protocolo.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"protocolo": {"type": "string", "description": "Ex.: OC-20261030-0007"}},
            "required": ["protocolo"],
            "additionalProperties": False,
        },
    },
]


def executar_ferramenta(nome: str, argumentos: dict) -> dict:
    if nome == "registrar_ocorrencia":
        return registrar_ocorrencia_por_voz(**argumentos)
    if nome == "consultar_ocorrencia":
        return consultar_ocorrencia(**argumentos)
    return {"ok": False, "erro": f"ferramenta desconhecida: {nome}"}
