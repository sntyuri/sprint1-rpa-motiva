import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const COR = {
  fundo: "#0d1526",
  painel: "#16213a",
  painel2: "#1d2b4a",
  borda: "#2a3a5e",
  texto: "#e8edf7",
  suave: "#93a3c4",
  destaque: "#f5a524",
  verde: "#3fbf7f",
  vermelho: "#ef5350",
  laranja: "#ff8a3d",
  amarelo: "#f2c94c",
  azul: "#4d9cff",
};

export const FONTE = "'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif";
export const MONO = "'Cascadia Code', 'Consolas', 'Courier New', monospace";

export const SEVERIDADE: Record<string, { cor: string; rotulo: string }> = {
  critica: { cor: COR.vermelho, rotulo: "CRÍTICA" },
  alta: { cor: COR.laranja, rotulo: "ALTA" },
  media: { cor: COR.amarelo, rotulo: "MÉDIA" },
  baixa: { cor: COR.verde, rotulo: "BAIXA" },
};

export const EQUIPE: Record<string, string> = {
  cco: "CCO", resgate: "Resgate", guincho: "Guincho", inspecao: "Inspeção",
  conservacao: "Conservação", ouvidoria: "Ouvidoria", triagem: "Supervisor",
};

export const CATEGORIA: Record<string, string> = {
  acidente: "Acidente", veiculo_avariado: "Veículo avariado", objeto_na_pista: "Objeto na pista",
  animal_na_pista: "Animal na pista", pedestre_na_pista: "Pedestre na pista", problema_na_via: "Problema na via",
  evento_ambiental: "Evento ambiental", atendimento_usuario: "Atendimento ao usuário", nao_e_ocorrencia: "Não é ocorrência",
};

/** 0 → 1 com mola, começando no frame `inicio`. */
export const useEntrada = (inicio = 0, amortecimento = 18) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - inicio, fps, config: { damping: amortecimento } });
};

export const Fundo: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: `radial-gradient(circle at 20% 10%, #18264a 0%, ${COR.fundo} 60%)`, fontFamily: FONTE, color: COR.texto }}>
    {children}
  </AbsoluteFill>
);

export const Aparece: React.FC<{ inicio?: number; de?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ inicio = 0, de = 30, children, style }) => {
  const p = useEntrada(inicio);
  return <div style={{ opacity: p, transform: `translateY(${(1 - p) * de}px)`, ...style }}>{children}</div>;
};

export const Titulo: React.FC<{ etapa?: string; children: React.ReactNode }> = ({ etapa, children }) => (
  <div style={{ position: "absolute", top: 60, left: 90, right: 90 }}>
    {etapa && <Aparece><div style={{ color: COR.destaque, fontSize: 26, fontWeight: 700, letterSpacing: 3, textTransform: "uppercase" }}>{etapa}</div></Aparece>}
    <Aparece inicio={4}><div style={{ fontSize: 58, fontWeight: 700, marginTop: 8 }}>{children}</div></Aparece>
  </div>
);

export const Cartao: React.FC<{ style?: React.CSSProperties; children: React.ReactNode }> = ({ style, children }) => (
  <div style={{ background: COR.painel, border: `1px solid ${COR.borda}`, borderRadius: 18, padding: 28, boxShadow: "0 20px 50px rgba(0,0,0,.35)", ...style }}>
    {children}
  </div>
);

export const Chip: React.FC<{ cor: string; children: React.ReactNode; cheio?: boolean; tamanho?: number }> = ({ cor, children, cheio, tamanho = 22 }) => (
  <span style={{
    display: "inline-block", padding: "5px 14px", borderRadius: 999, fontSize: tamanho, fontWeight: 700,
    color: cheio ? "#0d1526" : cor, background: cheio ? cor : `${cor}22`, border: `1.5px solid ${cor}`, marginRight: 10, marginBottom: 8,
  }}>{children}</span>
);

/** Terminal que mostra as linhas aos poucos: cada linha tem o frame em que aparece. */
export const Terminal: React.FC<{ linhas: { t: number; texto: string; cor?: string }[]; style?: React.CSSProperties; titulo?: string }> = ({ linhas, style, titulo = "terminal" }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ background: "#0a0f1c", border: `1px solid ${COR.borda}`, borderRadius: 14, overflow: "hidden", boxShadow: "0 20px 50px rgba(0,0,0,.4)", ...style }}>
      <div style={{ background: "#151d30", padding: "10px 16px", display: "flex", gap: 8, alignItems: "center" }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((c) => <div key={c} style={{ width: 13, height: 13, borderRadius: 7, background: c }} />)}
        <span style={{ color: COR.suave, fontSize: 18, marginLeft: 12, fontFamily: MONO }}>{titulo}</span>
      </div>
      <div style={{ padding: "18px 22px", fontFamily: MONO, fontSize: 23, lineHeight: 1.55 }}>
        {linhas.filter((l) => frame >= l.t).map((l, i) => {
          const digitado = l.texto.startsWith("$ ")
            ? l.texto.slice(0, Math.max(2, Math.floor((frame - l.t) * 1.6)))
            : l.texto;
          return <div key={i} style={{ color: l.cor ?? COR.texto, whiteSpace: "pre-wrap" }}>{digitado}</div>;
        })}
      </div>
    </div>
  );
};

export const Rodape: React.FC = () => (
  <div style={{ position: "absolute", bottom: 26, right: 40, fontSize: 18, color: COR.suave, display: "flex", alignItems: "center", gap: 10 }}>
    <div style={{ width: 10, height: 10, borderRadius: 5, background: COR.verde }} />
    Dados da execução real do robô · 30/10/2026
  </div>
);

export const Seta: React.FC<{ progresso: number; largura?: number }> = ({ progresso, largura = 70 }) => (
  <div style={{ width: largura, height: 4, background: COR.borda, position: "relative", margin: "0 14px" }}>
    <div style={{ width: `${progresso * 100}%`, height: 4, background: COR.destaque }} />
    <div style={{ position: "absolute", right: -2, top: -7, width: 0, height: 0, borderTop: "9px solid transparent", borderBottom: "9px solid transparent", borderLeft: `14px solid ${progresso > 0.95 ? COR.destaque : COR.borda}` }} />
  </div>
);

export const progresso = (frame: number, inicio: number, dur: number) =>
  interpolate(frame, [inicio, inicio + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
