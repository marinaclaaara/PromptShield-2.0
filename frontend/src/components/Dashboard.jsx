import { formatarPercentual, histogramaRisco, resumir } from "../lib/stats.js";

const ROTULO = { ALLOW: "Permitido", REVIEW: "Revisar", BLOCK: "Bloqueado" };

/** Gráfico de barras desenhado em SVG puro (sem biblioteca de gráficos). */
function Barras({ titulo, rotulos, valores, classes }) {
  const max = Math.max(1, ...valores);
  const w = 360, h = 140, base = 112, largura = w / valores.length;
  return (
    <figure>
      <figcaption>{titulo}</figcaption>
      <svg viewBox={`0 0 ${w} ${h}`} className="grafico" role="img" aria-label={titulo}>
        {valores.map((v, i) => {
          const altura = (v / max) * 90;
          return (
            <g key={i}>
              <rect x={i * largura + 6} y={base - altura} width={largura - 12} height={altura} rx="3" className={classes[i]} />
              <text x={i * largura + largura / 2} y={base - altura - 4} textAnchor="middle" className="val">{v}</text>
              <text x={i * largura + largura / 2} y={base + 14} textAnchor="middle" className="rot">{rotulos[i]}</text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}

export default function Dashboard({ historico }) {
  if (!historico.length) return <p className="vazio">O dashboard aparece depois da primeira análise.</p>;
  const r = resumir(historico);
  const faixas = histogramaRisco(historico, 10);
  return (
    <section className="card">
      <h2>Estatísticas desta sessão e histórico local</h2>
      <div className="cartoes">
        <div><b>{r.total}</b><span>análises</span></div>
        <div><b>{formatarPercentual(r.taxaSuspeitos)}</b><span>revisar ou bloquear</span></div>
        <div><b>{formatarPercentual(r.mediaRisco)}</b><span>risco médio</span></div>
      </div>
      <div className="graficos">
        <Barras titulo="Decisões" rotulos={Object.keys(r.contagem).map((k) => ROTULO[k])}
                valores={Object.values(r.contagem)} classes={["f-ALLOW", "f-REVIEW", "f-BLOCK"]} />
        <Barras titulo="Distribuição do risco (faixas de 10%)" rotulos={faixas.map((_, i) => `${i * 10}`)}
                valores={faixas} classes={faixas.map(() => "f-REVIEW")} />
      </div>
    </section>
  );
}
