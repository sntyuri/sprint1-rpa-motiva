"""Linha de comando do robô: python -m motiva_rpa <comando>."""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from . import captura_arquivo, captura_email, config, pipeline, registro, voz

console = Console()
CORES = {"critica": "bold red", "alta": "red", "media": "yellow", "baixa": "green"}


def _mostrar(resultados: list[dict]) -> None:
    for r in resultados:
        if "erro" in r:
            console.print(f"[yellow]{r['protocolo']}[/] registrada sem IA ({r['erro']}), aguardando triagem manual")
            continue
        c = r["classificacao"]
        console.print(f"[bold]{r['protocolo']}[/] [{CORES[c['severidade']]}]{c['severidade'].upper()}[/] "
                      f"{c['categoria']} -> {', '.join(r['equipes'])} ({r['status']}, até {r['prazo']})")
        console.print(f"   {c['resumo']}", style="dim")


def cmd_criar_caixa(_):
    caixa = captura_email.CaixaTemporaria.criar()
    console.print(f"Caixa criada. Envie as solicitações para: [bold cyan]{caixa.endereco}[/]")


def cmd_rodar(args):
    caixa = captura_email.CaixaTemporaria.carregar()
    console.rule("Robô de triagem de ocorrências")
    console.print(f"E-mail monitorado: [cyan]{caixa.endereco if caixa else 'nenhum (rode criar-caixa)'}[/]")
    console.print(f"Pasta monitorada: [cyan]{config.PASTA_ENTRADA}[/]")
    console.print(f"Modelo de IA: [cyan]{config.MODELO_IA}[/]  |  Ctrl+C para parar\n")
    while True:
        try:
            _mostrar(captura_email.verificar_caixa())
            _mostrar(captura_arquivo.varrer_pasta())
        except Exception:
            logging.getLogger("motiva_rpa").exception("Falha no ciclo; tento de novo no próximo")
        if args.uma_vez:
            break
        time.sleep(args.intervalo)


def cmd_processar_arquivo(args):
    _mostrar(captura_arquivo.processar_arquivo(Path(args.caminho)))


def cmd_processar_texto(args):
    r = pipeline.processar(args.texto, canal=args.canal)
    _mostrar([r] if r else [])


def cmd_voz(args):
    console.print_json(json.dumps(voz.registrar_ocorrencia_por_voz(args.transcricao, args.telefone, args.local),
                                  ensure_ascii=False))


def cmd_consultar(args):
    console.print_json(json.dumps(voz.consultar_ocorrencia(args.protocolo), ensure_ascii=False))


def cmd_listar(args):
    tabela = Table(title="Ocorrências registradas")
    for col in ["Protocolo", "Canal", "Categoria", "Sev.", "Local", "Equipes", "Status", "Conf."]:
        tabela.add_column(col)
    for oc in registro.listar(args.n):
        local = " ".join(str(x) for x in [oc["rodovia"], f"km {oc['km']:g}" if oc["km"] is not None else None] if x)
        sev = oc["severidade"] or "-"
        tabela.add_row(oc["protocolo"], oc["canal"], oc["categoria"] or "-", f"[{CORES.get(sev, '')}]{sev}[/]",
                       local or "-", ", ".join(json.loads(oc["equipes"] or "[]")), oc["status"],
                       f"{oc['confianca']:.0%}" if oc["confianca"] is not None else "-")
    console.print(tabela)


def cmd_exportar(_):
    console.print(f"Planilha gerada: {registro.exportar_excel()}")


def main(argv=None):
    # O console do Windows não usa UTF-8 por padrão e estraga os acentos.
    for fluxo in (sys.stdout, sys.stderr):
        if fluxo.encoding and fluxo.encoding.lower() != "utf-8":
            fluxo.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="%H:%M:%S",
                        handlers=[RichHandler(console=console, show_path=False)])
    for barulhento in ("httpx", "httpx2", "httpcore", "anthropic"):
        logging.getLogger(barulhento).setLevel(logging.WARNING)
    config.garantir_pastas()

    p = argparse.ArgumentParser(prog="python -m motiva_rpa", description="Robô de triagem de ocorrências rodoviárias")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("criar-caixa", help="cria a caixa de e-mail temporária (Guerrilla Mail)").set_defaults(f=cmd_criar_caixa)

    s = sub.add_parser("rodar", help="monitora e-mail e pasta entrada/ continuamente")
    s.add_argument("--intervalo", type=int, default=config.INTERVALO_SEGUNDOS)
    s.add_argument("--uma-vez", action="store_true", help="faz um ciclo só e sai")
    s.set_defaults(f=cmd_rodar)

    s = sub.add_parser("processar-arquivo", help="processa uma planilha específica")
    s.add_argument("caminho")
    s.set_defaults(f=cmd_processar_arquivo)

    s = sub.add_parser("processar-texto", help="processa uma solicitação digitada")
    s.add_argument("texto")
    s.add_argument("--canal", default="manual")
    s.set_defaults(f=cmd_processar_texto)

    s = sub.add_parser("voz", help="simula a chamada do agente de voz")
    s.add_argument("transcricao")
    s.add_argument("--telefone")
    s.add_argument("--local")
    s.set_defaults(f=cmd_voz)

    s = sub.add_parser("consultar", help="consulta um protocolo (como o agente de voz faria)")
    s.add_argument("protocolo")
    s.set_defaults(f=cmd_consultar)

    s = sub.add_parser("listar", help="mostra as últimas ocorrências")
    s.add_argument("-n", type=int, default=20)
    s.set_defaults(f=cmd_listar)

    sub.add_parser("exportar", help="gera saida/ocorrencias.xlsx").set_defaults(f=cmd_exportar)

    args = p.parse_args(argv)
    args.f(args)
