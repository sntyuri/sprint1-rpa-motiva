"""Classificação da solicitação e extração dos dados do registro com o Claude.

A resposta vem presa a um JSON Schema (structured outputs), então o restante do
robô sempre recebe os mesmos campos, mesmo quando o relato é bagunçado.
"""
import json

import anthropic

from . import config

CATEGORIAS = [
    "acidente",            # colisão, capotamento, atropelamento, saída de pista
    "veiculo_avariado",    # pane, pneu furado, falta de combustível, superaquecimento
    "objeto_na_pista",     # pneu, carga caída, galho, destroços
    "animal_na_pista",
    "pedestre_na_pista",
    "problema_na_via",     # buraco, sinalização, iluminação, defensa, erosão
    "evento_ambiental",    # incêndio às margens, alagamento, neblina forte, queda de barreira
    "atendimento_usuario", # pedágio, cobrança, reclamação, elogio, pedido de informação
    "nao_e_ocorrencia",    # spam, teste, mensagem sem relação com a rodovia
]

SEVERIDADES = ["critica", "alta", "media", "baixa"]

PROMPT_SISTEMA = """Você faz a triagem das solicitações que chegam ao Centro de Controle Operacional de uma concessionária de rodovias (Motiva). As mensagens vêm de usuários da rodovia, de equipes de campo e de outras áreas, por e-mail, planilha ou ligação transcrita. Costumam ser curtas, informais, com erros de digitação e sem todos os dados.

Para cada mensagem:
1. Escolha a categoria que descreve o que precisa ser feito na rodovia. Se houver mais de um problema, fique com o mais grave (ex.: acidente com destroços na pista é "acidente").
2. Defina a severidade:
   - critica: risco imediato à vida (vítima presa ou inconsciente, atropelamento, incêndio, veículo na contramão, pista bloqueada em alta velocidade);
   - alta: risco de novo acidente ou pista obstruída (objeto ou animal na faixa, veículo parado na faixa, acidente sem vítima grave);
   - media: situação que precisa de atendimento mas sem risco imediato (veículo no acostamento, buraco, sinalização apagada);
   - baixa: assuntos administrativos (cobrança de pedágio, reclamação, elogio, pedido de informação).
3. Extraia só o que estiver escrito ou for dedução direta. Não invente quilômetro, rodovia, nome ou telefone. Campo ausente fica null; vítimas sem menção ficam "nao_informado".
4. Em informacoes_faltantes, liste em português o que um atendente precisaria perguntar para agir (ex.: "quilômetro", "sentido da pista", "se há vítimas"). Lista vazia se não faltar nada importante.
5. confianca vai de 0 a 1 e mede o quanto você tem certeza da categoria. Use menos de 0.6 quando a mensagem for vaga, contraditória ou puder ser de duas categorias.
6. resumo: uma frase curta e objetiva para o painel do operador, sem repetir saudações.
7. justificativa: uma frase dizendo por que escolheu a categoria e a severidade."""

_texto_ou_nulo = {"anyOf": [{"type": "string"}, {"type": "null"}]}
_inteiro_ou_nulo = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
_numero_ou_nulo = {"anyOf": [{"type": "number"}, {"type": "null"}]}


def _objeto(propriedades: dict) -> dict:
    return {"type": "object", "properties": propriedades,
            "required": list(propriedades), "additionalProperties": False}


ESQUEMA = _objeto({
    "categoria": {"type": "string", "enum": CATEGORIAS},
    "subtipo": {"type": "string", "description": "Detalhe curto, ex.: 'capotamento', 'pneu na faixa', 'cobrança em duplicidade'"},
    "severidade": {"type": "string", "enum": SEVERIDADES},
    "risco_a_vida": {"type": "boolean"},
    "resumo": {"type": "string"},
    "local": _objeto({
        "rodovia": _texto_ou_nulo,
        "km": _numero_ou_nulo,
        "sentido": _texto_ou_nulo,
        "referencia": _texto_ou_nulo,
    }),
    "veiculos_envolvidos": _inteiro_ou_nulo,
    "vitimas": _objeto({
        "ha_vitimas": {"type": "string", "enum": ["sim", "nao", "nao_informado"]},
        "quantidade": _inteiro_ou_nulo,
        "descricao": _texto_ou_nulo,
    }),
    "pista_bloqueada": {"type": "string", "enum": ["total", "parcial", "nao", "nao_informado"]},
    "solicitante": _objeto({
        "nome": _texto_ou_nulo,
        "telefone": _texto_ou_nulo,
        "email": _texto_ou_nulo,
    }),
    "informacoes_faltantes": {"type": "array", "items": {"type": "string"}},
    "confianca": {"type": "number"},
    "justificativa": {"type": "string"},
})

# Modelos que aceitam o fallback automático do lado do servidor quando recusam um pedido.
_COM_FALLBACK = ("claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5")


class ErroIA(Exception):
    pass


_cliente = None


def _cliente_api() -> anthropic.Anthropic:
    global _cliente
    if _cliente is None:
        _cliente = anthropic.Anthropic()
    return _cliente


def classificar(texto: str, canal: str, contexto: str = "") -> dict:
    """Devolve a classificação e os campos extraídos de uma solicitação em texto livre."""
    conteudo = f"Canal de entrada: {canal}\n"
    if contexto:
        conteudo += f"Dados que vieram junto com a mensagem:\n{contexto}\n"
    conteudo += f"\nMensagem:\n<mensagem>\n{texto.strip()}\n</mensagem>"

    extras = {}
    if config.MODELO_IA in _COM_FALLBACK:
        extras = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}

    try:
        resposta = _cliente_api().beta.messages.create(
            model=config.MODELO_IA,
            max_tokens=4000,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": conteudo}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": ESQUEMA}},
            **extras,
        )
    except anthropic.AuthenticationError as e:
        raise ErroIA("Chave da API inválida ou ausente (ANTHROPIC_API_KEY no .env).") from e
    except anthropic.RateLimitError as e:
        raise ErroIA("Limite de uso da API atingido; tente de novo em instantes.") from e
    except anthropic.APIStatusError as e:
        raise ErroIA(f"A API respondeu com erro {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise ErroIA("Sem conexão com a API da Anthropic.") from e

    if resposta.stop_reason == "refusal":
        raise ErroIA("O modelo se recusou a processar a mensagem.")
    if resposta.stop_reason == "max_tokens":
        raise ErroIA("A resposta da IA foi cortada (max_tokens).")

    texto_json = next(b.text for b in resposta.content if b.type == "text")
    dados = json.loads(texto_json)
    dados["confianca"] = max(0.0, min(1.0, float(dados["confianca"])))
    dados["_modelo"] = resposta.model
    return dados
