import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import dados from "./dados.json";
import {
  Aparece, CATEGORIA, COR, Cartao, Chip, EQUIPE, FONTE, Fundo, MONO, Rodape, SEVERIDADE, Seta, Terminal, Titulo,
  progresso, useEntrada,
} from "./ui";

type Oc = (typeof dados.ocorrencias)[number];
const porProtocolo = (p: string) => dados.ocorrencias.find((o) => o.protocolo === p) as Oc;
const s = (seg: number) => Math.round(seg * 30);

const EMAIL = porProtocolo("OC-20261030-0002");
const PLANILHA = ["0006", "0007", "0008", "0009", "0010", "0011", "0012"].map((n) => porProtocolo(`OC-20261030-${n}`));
const VOZ = porProtocolo("OC-20261030-0013");

const local = (o: Oc) => [o.rodovia, o.km != null ? `km ${String(o.km).replace(".", ",")}` : null, o.sentido ? `sentido ${o.sentido}` : null]
  .filter(Boolean).join(" · ");

// ---------------------------------------------------------------- 1. Abertura
export const Abertura: React.FC = () => {
  const p = useEntrada(0, 14);
  return (
    <Fundo>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}>
        <div style={{ opacity: p, transform: `scale(${0.9 + p * 0.1})` }}>
          <div style={{ color: COR.destaque, fontSize: 30, letterSpacing: 6, fontWeight: 700 }}>RPA · SPRINT 1</div>
          <div style={{ fontSize: 92, fontWeight: 800, marginTop: 18, lineHeight: 1.05 }}>Robô de triagem de<br />ocorrências rodoviárias</div>
          <div style={{ fontSize: 34, color: COR.suave, marginTop: 26 }}>Receber, entender e encaminhar · Plataforma Motiva</div>
        </div>
        <Aparece inicio={s(2.5)} style={{ position: "absolute", bottom: 80, fontSize: 24, color: COR.suave }}>
          Gabriel Muniz · Leonardo Barros · Marcelo Augusto · Rafael Tavares · Yuri Quirino
        </Aparece>
      </AbsoluteFill>
    </Fundo>
  );
};

// ---------------------------------------------------------------- 2. O problema
const DORES = [
  ["Fila única, lida quando dá", "No pico o atendente está no telefone e a caixa espera."],
  ["Sem prioridade", "Um acidente com vítima pode ficar atrás de três reclamações de pedágio."],
  ["Registro digitado à mão", "Um km errado manda a equipe para o lugar errado."],
  ["Equipe escolhida de cabeça", "O mesmo caso é tratado de jeitos diferentes em cada turno."],
];
export const Problema: React.FC = () => {
  const frame = useCurrentFrame();
  const fila = ["Reclamação de pedágio", "Elogio", "Reclamação de pedágio", "Acidente com vítima", "Buraco na pista"];
  return (
    <Fundo>
      <Titulo etapa="Antes da automação">Tudo cai numa caixa compartilhada</Titulo>
      <div style={{ position: "absolute", top: 270, left: 90, width: 640 }}>
        <Cartao>
          <div style={{ fontSize: 24, color: COR.suave, marginBottom: 16 }}>Caixa do CCO · 23 não lidas</div>
          {fila.map((t, i) => {
            const p = useEntrada(s(0.8) + i * 8);
            const grave = t.startsWith("Acidente");
            return (
              <div key={i} style={{
                opacity: p, transform: `translateX(${(1 - p) * -40}px)`, padding: "14px 18px", marginBottom: 10, borderRadius: 10,
                background: grave && frame > s(12.5) ? `${COR.vermelho}30` : COR.painel2, fontSize: 27,
                border: grave && frame > s(12.5) ? `2px solid ${COR.vermelho}` : `1px solid ${COR.borda}`,
              }}>
                ✉ {t} {grave && frame > s(12.5) && <span style={{ color: COR.vermelho, fontWeight: 700 }}> · há 18 min</span>}
              </div>
            );
          })}
        </Cartao>
      </div>
      <div style={{ position: "absolute", top: 270, left: 800, right: 90 }}>
        {DORES.map(([t, d], i) => (
          <Aparece key={t} inicio={s([5.8, 12, 20, 21.6][i])} style={{ marginBottom: 26 }}>
            <div style={{ fontSize: 34, fontWeight: 700 }}><span style={{ color: COR.vermelho }}>✕</span> {t}</div>
            <div style={{ fontSize: 26, color: COR.suave, marginTop: 4, marginLeft: 38 }}>{d}</div>
          </Aparece>
        ))}
      </div>
      <Aparece inicio={s(22)} style={{ position: "absolute", bottom: 50, left: 90, fontSize: 24, color: COR.suave }}>
        Processo "antes" segundo o nosso entendimento de um CCO; os tempos são estimativas.
      </Aparece>
    </Fundo>
  );
};

// ---------------------------------------------------------------- 3. A solução
const ETAPAS = [
  ["📥", "Captura", "e-mail e planilhas,\na cada 20 s"],
  ["🧠", "IA (Claude)", "categoria, gravidade,\nlocal, vítimas"],
  ["🗂", "Registro", "protocolo e\ncampos estruturados"],
  ["📣", "Encaminhamento", "equipes certas\ncom prazo"],
];
export const Solucao: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Fundo>
      <Titulo etapa="Depois da automação">O robô lê, a IA entende, a equipe recebe</Titulo>
      <div style={{ position: "absolute", top: 380, left: 0, right: 0, display: "flex", justifyContent: "center", alignItems: "center" }}>
        {ETAPAS.map(([icone, nome, desc], i) => (
          <React.Fragment key={nome}>
            {i > 0 && <Seta progresso={progresso(frame, s(3.5) + i * s(2.2) - 12, 12)} />}
            <Aparece inicio={s(3.5) + i * s(2.2)}>
              <Cartao style={{ width: 330, textAlign: "center", padding: 30 }}>
                <div style={{ fontSize: 64 }}>{icone}</div>
                <div style={{ fontSize: 34, fontWeight: 700, marginTop: 8 }}>{nome}</div>
                <div style={{ fontSize: 24, color: COR.suave, marginTop: 10, whiteSpace: "pre-line" }}>{desc}</div>
              </Cartao>
            </Aparece>
          </React.Fragment>
        ))}
      </div>
      <Aparece inicio={s(12)} style={{ position: "absolute", top: 760, left: 0, right: 0, textAlign: "center" }}>
        <span style={{ fontSize: 30, color: COR.suave }}>Quando a IA não tem certeza, </span>
        <span style={{ fontSize: 30, color: COR.destaque, fontWeight: 700 }}>um supervisor confirma antes de despachar.</span>
      </Aparece>
    </Fundo>
  );
};

// ---------------------------------------------------------------- 4. Robô ligado
export const RoboLigado: React.FC = () => (
  <Fundo>
    <Titulo etapa="Demonstração">Ligando o robô</Titulo>
    <Terminal style={{ position: "absolute", top: 270, left: 90, right: 90 }} linhas={[
      { t: 0, texto: "$ python -m motiva_rpa rodar", cor: COR.verde },
      { t: s(2.2), texto: "──────────── Robô de triagem de ocorrências ────────────", cor: COR.suave },
      { t: s(2.6), texto: `E-mail monitorado: ${dados.caixa}`, cor: COR.azul },
      { t: s(3.0), texto: "Pasta monitorada: sprint1-rpa\\entrada", cor: COR.azul },
      { t: s(3.4), texto: "Modelo de IA: claude-opus-5-5  |  Ctrl+C para parar", cor: COR.azul },
      { t: s(4.5), texto: "aguardando solicitações...", cor: COR.suave },
    ]} />
    <Rodape />
  </Fundo>
);

// ---------------------------------------------------------------- 5. E-mail chegando
const Campo: React.FC<{ rotulo: string; valor: React.ReactNode; inicio: number }> = ({ rotulo, valor, inicio }) => (
  <Aparece inicio={inicio} de={14} style={{ display: "flex", padding: "9px 0", borderBottom: `1px solid ${COR.borda}`, fontSize: 25 }}>
    <div style={{ width: 230, color: COR.suave }}>{rotulo}</div>
    <div style={{ flex: 1 }}>{valor}</div>
  </Aparece>
);

export const EmailChegando: React.FC = () => {
  const frame = useCurrentFrame();
  const voa = interpolate(frame, [s(4.5), s(5.5)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const sev = SEVERIDADE[EMAIL.severidade];
  return (
    <Fundo>
      <Titulo etapa="Captura por e-mail">Um e-mail de verdade chega na caixa</Titulo>
      {/* e-mail enviado de uma conta Gmail */}
      <div style={{ position: "absolute", top: 260, left: 90, width: 760, opacity: 1 - voa * 0.55, transform: `translateX(${voa * 30}px)` }}>
        <Cartao style={{ background: "#f6f8fc", color: "#1f2937" }}>
          <div style={{ fontSize: 20, color: "#5f6368" }}>De: kirino•••@gmail.com</div>
          <div style={{ fontSize: 20, color: "#5f6368" }}>Para: {dados.caixa}</div>
          <div style={{ fontSize: 26, fontWeight: 700, margin: "14px 0 10px" }}>acidente na anhanguera</div>
          <div style={{ fontSize: 23, lineHeight: 1.5 }}>{EMAIL.texto_original}</div>
        </Cartao>
      </div>
      <Terminal titulo="robô" style={{ position: "absolute", top: 260, left: 900, right: 90 }} linhas={[
        { t: s(5.6), texto: "21:22:01  E-mail recebido de kirino•••@gmail.com", cor: COR.azul },
        { t: s(7.0), texto: "21:22:06  OC-20261030-0002 | acidente/critica", cor: COR.verde },
        { t: s(7.2), texto: "          encaminhada -> cco, resgate, guincho", cor: COR.verde },
      ]} />
      {/* o que a IA extraiu */}
      <div style={{ position: "absolute", top: 520, left: 900, right: 90 }}>
        <Aparece inicio={s(7.5)}>
          <Cartao style={{ padding: "20px 28px" }}>
            <div style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 22, color: COR.suave, marginRight: 14 }}>A IA extraiu</span>
              <Chip cor={sev.cor} cheio>{sev.rotulo}</Chip>
              <Chip cor={COR.azul}>{CATEGORIA[EMAIL.categoria]}</Chip>
              <span style={{ marginLeft: "auto", fontSize: 22, color: COR.suave }}>confiança {Math.round(EMAIL.confianca * 100)}%</span>
            </div>
            <Campo inicio={s(8.5)} rotulo="Local" valor={local(EMAIL)} />
            <Campo inicio={s(9.5)} rotulo="Vítimas" valor={`${EMAIL.ha_vitimas}${EMAIL.qtd_vitimas ? ` (${EMAIL.qtd_vitimas})` : ""} · ${EMAIL.subtipo}`} />
            <Campo inicio={s(10.5)} rotulo="Pista bloqueada" valor={EMAIL.pista_bloqueada} />
            <Campo inicio={s(11.5)} rotulo="Contato" valor={`${EMAIL.solicitante_nome ?? "-"} · ${EMAIL.solicitante_telefone ?? "-"}`} />
            <Campo inicio={s(15.3)} rotulo="Confirmar" valor={EMAIL.informacoes_faltantes.slice(0, 3).join("; ")} />
          </Cartao>
        </Aparece>
      </div>
      <div style={{ position: "absolute", top: 680, left: 90, width: 760 }}>
        <Aparece inicio={s(20.5)}><div style={{ fontSize: 24, color: COR.suave, marginBottom: 12 }}>Equipes acionadas pelas regras de encaminhamento</div></Aparece>
        {EMAIL.equipes.map((e, i) => (
          <Aparece key={e} inicio={s(21) + i * 10} style={{ display: "inline-block" }}>
            <Chip cor={COR.destaque} cheio tamanho={28}>→ {EQUIPE[e]}</Chip>
          </Aparece>
        ))}
      </div>
      <Rodape />
    </Fundo>
  );
};

// ---------------------------------------------------------------- 6. Aviso que a equipe recebe
export const AvisoEquipe: React.FC = () => {
  const linhas = dados.aviso_resgate.corpo.split("\n").slice(0, 16);
  return (
    <Fundo>
      <Titulo etapa="Encaminhamento">O aviso que o resgate recebe</Titulo>
      <Aparece inicio={s(0.8)} style={{ position: "absolute", top: 250, left: 160, right: 160 }}>
        <Cartao style={{ background: "#f6f8fc", color: "#1f2937", padding: 34 }}>
          <div style={{ fontSize: 26, fontWeight: 700, color: "#b42318", marginBottom: 14 }}>{dados.aviso_resgate.assunto}</div>
          {linhas.map((l, i) => (
            <Aparece key={i} inicio={s(1.5) + i * 4} de={8}>
              <div style={{ fontSize: 23, lineHeight: 1.45, minHeight: 14, fontWeight: /^(Resumo|Atender|Confirmar)/.test(l) ? 700 : 400 }}>{l || " "}</div>
            </Aparece>
          ))}
        </Cartao>
      </Aparece>
      <Rodape />
    </Fundo>
  );
};

// ---------------------------------------------------------------- 7. Planilha
export const Planilha: React.FC = () => {
  const frame = useCurrentFrame();
  const entra = useEntrada(s(0.6));
  return (
    <Fundo>
      <Titulo etapa="Captura por planilha">A planilha do turno, com 7 relatos</Titulo>
      <div style={{ position: "absolute", top: 250, left: 90, right: 90, opacity: entra, transform: `translateY(${(1 - entra) * 40}px)` }}>
        <div style={{ fontSize: 22, color: COR.suave, marginBottom: 12, fontFamily: MONO }}>entrada\planilha_ocorrencias_exemplo.xlsx</div>
        {PLANILHA.map((o, i) => {
          const t = s(4) + i * s(1.4);
          const pronto = frame >= t;
          const sev = SEVERIDADE[o.severidade];
          const duvida = o.confianca < 0.6;
          const destaque = duvida && frame > s(15);
          return (
            <div key={o.protocolo} style={{
              display: "flex", alignItems: "center", gap: 18, padding: "12px 18px", marginBottom: 8, borderRadius: 10,
              background: destaque ? `${COR.destaque}22` : COR.painel, border: `${destaque ? 2 : 1}px solid ${destaque ? COR.destaque : COR.borda}`,
            }}>
              <div style={{ flex: 1, fontSize: 21, color: pronto ? COR.texto : COR.suave, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {o.texto_original}
              </div>
              <div style={{ width: 760, display: "flex", alignItems: "center", opacity: pronto ? progresso(frame, t, 10) : 0 }}>
                <div style={{ width: 140 }}><Chip cor={sev.cor} cheio tamanho={18}>{sev.rotulo}</Chip></div>
                <span style={{ fontSize: 20, width: 230 }}>{CATEGORIA[o.categoria]}</span>
                <span style={{ fontSize: 20, color: COR.destaque, flex: 1 }}>→ {o.equipes.map((e) => EQUIPE[e]).join(", ")}</span>
                <span style={{ fontSize: 20, color: duvida ? COR.destaque : COR.suave, width: 70, textAlign: "right", fontWeight: duvida ? 700 : 400 }}>
                  {Math.round(o.confianca * 100)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
      <Aparece inicio={s(21.3)} style={{ position: "absolute", bottom: 90, left: 90, right: 90 }}>
        <Cartao style={{ borderColor: COR.destaque, padding: "18px 26px", fontSize: 27 }}>
          <b style={{ color: COR.destaque }}>"Vi umas luzes piscando, não sei se é acidente ou obra"</b>: a IA ficou com 30% de confiança,
          então o caso foi para o supervisor confirmar antes de alguém sair.
        </Cartao>
      </Aparece>
      <Rodape />
    </Fundo>
  );
};

// ---------------------------------------------------------------- 8. Registro
export const Registro: React.FC = () => (
  <Fundo>
    <Titulo etapa="Registro estruturado">Tudo com protocolo, exportável para Excel</Titulo>
    <div style={{ position: "absolute", top: 250, left: 90, right: 90 }}>
      <Aparece inicio={s(0.6)}>
        <div style={{ display: "flex", fontSize: 19, color: COR.suave, padding: "0 14px 10px", fontWeight: 700 }}>
          <div style={{ width: 230 }}>Protocolo</div><div style={{ width: 110 }}>Canal</div><div style={{ width: 280 }}>Categoria</div>
          <div style={{ width: 130 }}>Gravidade</div><div style={{ flex: 1 }}>Local</div><div style={{ width: 300 }}>Equipes</div>
        </div>
      </Aparece>
      {dados.ocorrencias.map((o, i) => (
        <Aparece key={o.protocolo} inicio={s(1) + i * 5} de={10}>
          <div style={{ display: "flex", alignItems: "center", fontSize: 20, padding: "8px 14px", background: i % 2 ? COR.painel : COR.painel2, borderRadius: 6 }}>
            <div style={{ width: 230, fontFamily: MONO, fontSize: 18 }}>{o.protocolo}</div>
            <div style={{ width: 110, color: COR.suave }}>{o.canal}</div>
            <div style={{ width: 280 }}>{CATEGORIA[o.categoria]}</div>
            <div style={{ width: 130, color: SEVERIDADE[o.severidade].cor, fontWeight: 700 }}>{SEVERIDADE[o.severidade].rotulo}</div>
            <div style={{ flex: 1, color: COR.suave, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", paddingRight: 16 }}>{local(o) || "não informado"}</div>
            <div style={{ width: 300, color: COR.destaque }}>{o.equipes.map((e) => EQUIPE[e]).join(", ")}</div>
          </div>
        </Aparece>
      ))}
    </div>
    <Rodape />
  </Fundo>
);

// ---------------------------------------------------------------- 9. Agente de voz
export const Voz: React.FC = () => {
  const v = dados.voz;
  return (
    <Fundo>
      <Titulo etapa="Próxima sprint">A função que o agente de voz vai chamar</Titulo>
      <Terminal style={{ position: "absolute", top: 260, left: 90, width: 860 }} linhas={[
        { t: 0, texto: `$ python -m motiva_rpa voz "${VOZ.texto_original}"`, cor: COR.verde },
      ]} />
      <div style={{ position: "absolute", top: 470, left: 90, width: 860 }}>
        <Aparece inicio={s(5.8)}>
          <Cartao style={{ fontFamily: MONO, fontSize: 21, lineHeight: 1.55, padding: 24 }}>
            <div><span style={{ color: COR.suave }}>protocolo:</span> {v.protocolo}</div>
            <div><span style={{ color: COR.suave }}>categoria:</span> {v.categoria} · {v.severidade}</div>
            <div><span style={{ color: COR.suave }}>equipes_acionadas:</span> <span style={{ color: COR.destaque }}>{v.equipes_acionadas.join(", ")}</span></div>
            <div style={{ marginTop: 10, color: COR.suave }}>perguntas_pendentes:</div>
            {v.perguntas_pendentes.map((q, i) => (
              <Aparece key={q} inicio={s(11) + i * 8} de={8}><div>  • {q}</div></Aparece>
            ))}
          </Cartao>
        </Aparece>
      </div>
      <div style={{ position: "absolute", top: 380, left: 1020, right: 90 }}>
        <Aparece inicio={s(16.3)}>
          <div style={{ fontSize: 24, color: COR.suave, marginBottom: 14 }}>🔊 O que o agente fala para quem ligou</div>
          <div style={{ background: COR.destaque, color: "#1a1a1a", borderRadius: "28px 28px 28px 6px", padding: "28px 32px", fontSize: 32, lineHeight: 1.4, fontWeight: 600 }}>
            {v.fala_sugerida}
          </div>
        </Aparece>
        <Aparece inicio={s(18.6)} style={{ marginTop: 30, fontSize: 25, color: COR.suave, lineHeight: 1.5 }}>
          Na próxima sprint, o agente usa a lista de perguntas pendentes para continuar a ligação: quilômetro, sentido, se a pista está bloqueada.
        </Aparece>
      </div>
      <Rodape />
    </Fundo>
  );
};

// ---------------------------------------------------------------- 10. Quem decide o quê
const PAPEIS = [
  ["🧠", "IA", "Lê o texto livre e extrai os campos, com nota de confiança.", COR.azul],
  ["📋", "Regras", "Escolhem equipe e prazo. A operação audita e muda sem mexer na IA.", COR.destaque],
  ["🧑‍💼", "Supervisor", "Confirma quando a IA tem dúvida. Se a API cair, nada se perde.", COR.verde],
];
export const QuemDecide: React.FC = () => (
  <Fundo>
    <Titulo etapa="Quem decide o quê">A IA interpreta. Quem decide é a operação.</Titulo>
    <div style={{ position: "absolute", top: 330, left: 90, right: 90, display: "flex", gap: 40 }}>
      {PAPEIS.map(([icone, nome, desc, cor], i) => (
        <Aparece key={nome} inicio={s([3.9, 11.2, 22.9][i])} style={{ flex: 1 }}>
          <Cartao style={{ borderTop: `6px solid ${cor}`, minHeight: 380, padding: 36 }}>
            <div style={{ fontSize: 72 }}>{icone}</div>
            <div style={{ fontSize: 42, fontWeight: 800, marginTop: 10, color: cor }}>{nome}</div>
            <div style={{ fontSize: 30, color: COR.texto, marginTop: 16, lineHeight: 1.4 }}>{desc}</div>
          </Cartao>
        </Aparece>
      ))}
    </div>
  </Fundo>
);

// ---------------------------------------------------------------- 11. Encerramento
export const Encerramento: React.FC = () => (
  <Fundo>
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center", fontFamily: FONTE }}>
      <Aparece>
        <div style={{ fontSize: 30, color: COR.destaque, letterSpacing: 5, fontWeight: 700 }}>RESUMO</div>
      </Aparece>
      {[
        "Captura por e-mail e por planilha, a cada 20 segundos",
        "Claude classifica e extrai os dados do registro",
        "Registro com protocolo e aviso para as equipes certas",
        "Função pronta para o agente de voz",
      ].map((t, i) => (
        <Aparece key={t} inicio={s(0.6) + i * 12} style={{ fontSize: 40, marginTop: 22 }}>
          <span style={{ color: COR.verde }}>✓</span> {t}
        </Aparece>
      ))}
      <Aparece inicio={s(5)} style={{ marginTop: 60, fontSize: 26, color: COR.suave }}>
        Código, documentação e desenho do processo no repositório do grupo
      </Aparece>
    </AbsoluteFill>
  </Fundo>
);

export const CENAS: { id: string; seg: number; C: React.FC }[] = [
  { id: "abertura", seg: 4.9, C: Abertura },
  { id: "problema", seg: 23.5, C: Problema },
  { id: "solucao", seg: 14.1, C: Solucao },
  { id: "robo", seg: 5.8, C: RoboLigado },
  { id: "email", seg: 26.7, C: EmailChegando },
  { id: "aviso", seg: 10.8, C: AvisoEquipe },
  { id: "planilha", seg: 29.3, C: Planilha },
  { id: "registro", seg: 7.3, C: Registro },
  { id: "voz", seg: 21, C: Voz },
  { id: "decide", seg: 32.4, C: QuemDecide },
  { id: "fim", seg: 11, C: Encerramento },
];
