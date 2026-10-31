"""Testes do caminho captura -> registro -> encaminhamento sem chamar a API (a IA é simulada)."""
import json

import pandas as pd
import pytest

from motiva_rpa import captura_arquivo, config, encaminhamento, ia, pipeline, registro, voz


def classificacao(**mudancas):
    base = {
        "categoria": "objeto_na_pista", "subtipo": "pneu na faixa", "severidade": "alta", "risco_a_vida": False,
        "resumo": "Pneu de caminhão na faixa da esquerda", "local": {"rodovia": "SP-330", "km": 87.0, "sentido": "interior", "referencia": None},
        "veiculos_envolvidos": None, "vitimas": {"ha_vitimas": "nao_informado", "quantidade": None, "descricao": None},
        "pista_bloqueada": "parcial", "solicitante": {"nome": "Ana", "telefone": "11999990000", "email": None},
        "informacoes_faltantes": [], "confianca": 0.93, "justificativa": "Objeto na faixa de rolamento.", "_modelo": "teste",
    }
    base.update(mudancas)
    return base


@pytest.fixture(autouse=True)
def ambiente_isolado(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PASTA_ENTRADA", tmp_path / "entrada")
    monkeypatch.setattr(config, "PASTA_SAIDA", tmp_path / "saida")
    monkeypatch.setattr(config, "PASTA_DADOS", tmp_path / "dados")
    monkeypatch.setattr(config, "BANCO", tmp_path / "dados" / "teste.db")
    monkeypatch.setattr(config, "SMTP_HOST", "")
    monkeypatch.setattr(config, "WEBHOOK_URL", "")
    config.garantir_pastas()


@pytest.fixture
def ia_falsa(monkeypatch):
    respostas = []
    monkeypatch.setattr(ia, "classificar", lambda texto, canal, contexto="": respostas.pop(0))
    return respostas


# --- regras de encaminhamento ---

def test_acidente_com_vitima_aciona_resgate():
    eq = encaminhamento.definir_equipes(classificacao(categoria="acidente", severidade="critica", risco_a_vida=True,
                                                     vitimas={"ha_vitimas": "sim", "quantidade": 2, "descricao": None}))
    assert eq == ["cco", "resgate", "guincho"]


def test_acidente_sem_vitima_nao_aciona_resgate():
    eq = encaminhamento.definir_equipes(classificacao(categoria="acidente", severidade="alta",
                                                     vitimas={"ha_vitimas": "nao", "quantidade": None, "descricao": None}))
    assert "resgate" not in eq


def test_carro_no_acostamento_vai_so_para_o_guincho():
    eq = encaminhamento.definir_equipes(classificacao(categoria="veiculo_avariado", severidade="media", pista_bloqueada="nao"))
    assert eq == ["guincho"]


def test_animal_perigoso_sem_vitima_nao_aciona_resgate():
    eq = encaminhamento.definir_equipes(classificacao(categoria="animal_na_pista", severidade="alta", risco_a_vida=True))
    assert eq == ["inspecao", "cco"]


def test_pedagio_vai_para_ouvidoria():
    assert encaminhamento.definir_equipes(classificacao(categoria="atendimento_usuario", severidade="baixa")) == ["ouvidoria"]


def test_baixa_confianca_passa_por_triagem_humana():
    assert encaminhamento.precisa_triagem(classificacao(confianca=0.4), 0.6)
    assert not encaminhamento.precisa_triagem(classificacao(confianca=0.9), 0.6)


# --- caminho completo ---

def test_pipeline_registra_e_encaminha(ia_falsa):
    ia_falsa.append(classificacao())
    r = pipeline.processar("tem um pneu no meio da pista km 87", canal="email", origem_ref="email:abc")
    assert r["equipes"] == ["inspecao", "cco"] and r["status"] == "encaminhada"
    oc = registro.buscar(r["protocolo"])
    assert oc["categoria"] == "objeto_na_pista" and oc["km"] == 87.0
    assert (config.PASTA_SAIDA / "encaminhamentos" / "inspecao" / f"{r['protocolo']}.eml").exists()


def test_mesma_mensagem_nao_e_registrada_duas_vezes(ia_falsa):
    ia_falsa.append(classificacao())
    assert pipeline.processar("texto", canal="email", origem_ref="email:repetido")
    assert pipeline.processar("texto", canal="email", origem_ref="email:repetido") is None


def test_falha_da_ia_nao_perde_a_solicitacao(monkeypatch):
    def falha(*_, **__):
        raise ia.ErroIA("sem conexão")
    monkeypatch.setattr(ia, "classificar", falha)
    r = pipeline.processar("acidente no km 10", canal="email", origem_ref="email:x")
    assert registro.buscar(r["protocolo"])["status"] == "aguardando_triagem"


def test_planilha_com_coluna_acentuada(ia_falsa, tmp_path):
    arquivo = tmp_path / "relatos.csv"
    pd.DataFrame({"Descrição": ["buraco na pista", "pneu na faixa"], "Telefone": ["1199", ""]}).to_csv(
        arquivo, sep=";", index=False, encoding="utf-8-sig")
    ia_falsa += [classificacao(categoria="problema_na_via", severidade="media"), classificacao()]
    assert len(captura_arquivo.processar_arquivo(arquivo)) == 2


def test_planilha_sem_coluna_de_texto_da_erro_claro(tmp_path):
    arquivo = tmp_path / "ruim.csv"
    pd.DataFrame({"coluna_x": ["a"]}).to_csv(arquivo, index=False)
    with pytest.raises(ValueError, match="coluna de texto"):
        captura_arquivo.processar_arquivo(arquivo)


def test_pasta_entrada_move_arquivo_processado(ia_falsa):
    pd.DataFrame({"relato": ["animal na pista"]}).to_excel(config.PASTA_ENTRADA / "lote.xlsx", index=False)
    ia_falsa.append(classificacao(categoria="animal_na_pista"))
    captura_arquivo.varrer_pasta()
    assert not (config.PASTA_ENTRADA / "lote.xlsx").exists()
    assert len(list((config.PASTA_ENTRADA / "processados").iterdir())) == 1


# --- função do agente de voz ---

def test_voz_devolve_protocolo_fala_e_perguntas(ia_falsa):
    ia_falsa.append(classificacao(categoria="acidente", severidade="critica", risco_a_vida=True,
                                  informacoes_faltantes=["sentido da pista"]))
    r = voz.registrar_ocorrencia_por_voz("bateram aqui, tem gente machucada", telefone="11988887777")
    assert r["ok"] and r["protocolo"].startswith("OC-")
    assert "resgate" in r["equipes_acionadas"]
    assert "local seguro" in r["fala_sugerida"]
    assert r["perguntas_pendentes"] == ["sentido da pista"]
    consulta = voz.executar_ferramenta("consultar_ocorrencia", {"protocolo": r["protocolo"]})
    assert consulta["ok"] and consulta["status"] == "encaminhada"


def test_ferramentas_de_voz_tem_esquema_valido():
    for f in voz.FERRAMENTAS_VOZ:
        esquema = f["input_schema"]
        assert esquema["additionalProperties"] is False
        assert set(esquema["required"]) == set(esquema["properties"])
    json.dumps(voz.FERRAMENTAS_VOZ)


def test_esquema_da_ia_exige_todos_os_campos():
    def conferir(no):
        if no.get("type") == "object":
            assert set(no["required"]) == set(no["properties"]) and no["additionalProperties"] is False
            for filho in no["properties"].values():
                conferir(filho)
    conferir(ia.ESQUEMA)
