import { formatarPercentual } from "../lib/stats.js";

const ROTULO = { ALLOW: "Permitido", REVIEW: "Revisar", BLOCK: "Bloqueado" };

/** Barra de risco de 0 a 1, com marcas nos limiares (t1 = revisar, t2 = bloquear) quando conhecidos. */
export default function ResultCard({ resultado, limiares }) {
  if (!resultado) return null;
  const { decision, risk_score, trace_id, model_version, reason_codes } = resultado;
  return (
    <section className={`card resultado d-${decision}`} aria-live="polite">
      <div className="linha">
        <span className={`selo s-${decision}`}>{ROTULO[decision]}</span>
        <strong>Risco estimado: {formatarPercentual(risk_score)}</strong>
      </div>
      <svg viewBox="0 0 300 26" className="barra" role="img" aria-label={`Risco ${formatarPercentual(risk_score)}`}>
        <rect x="0" y="8" width="300" height="10" rx="5" className="trilho" />
        <rect x="0" y="8" width={300 * risk_score} height="10" rx="5" className={`preench f-${decision}`} />
        {limiares && [limiares.t1_review, limiares.t2_block].map((t, i) => (
          <g key={i}>
            <line x1={300 * t} x2={300 * t} y1="3" y2="23" className="marca" />
            <text x={300 * t} y="3" className="marca-txt" textAnchor="middle">{i === 0 ? "revisar" : "bloquear"}</text>
          </g>
        ))}
      </svg>
      <p className="nota">
        O risco é a probabilidade que o modelo atribui a "ataque". Não é uma garantia: o detector reduz o risco, não o elimina.
      </p>
      <dl className="meta">
        <dt>trace</dt><dd>{trace_id}</dd>
        <dt>modelo</dt><dd>{model_version}</dd>
        <dt>motivos</dt><dd>{reason_codes.length ? reason_codes.join(", ") : "nenhum"}</dd>
      </dl>
    </section>
  );
}
