const ROTULO = { ALLOW: "Permitido", REVIEW: "Revisar", BLOCK: "Bloqueado" };

export default function HistoryTable({ historico, aoLimpar }) {
  if (!historico.length) return <p className="vazio">Nenhuma análise ainda. Analise um texto na aba "Analisar".</p>;
  return (
    <section className="card">
      <div className="linha entre">
        <h2>Histórico ({historico.length})</h2>
        <button className="sec" onClick={aoLimpar}>Limpar histórico</button>
      </div>
      <p className="nota">Guardado apenas neste navegador. O texto completo não é enviado para nenhum outro lugar além da API.</p>
      <div className="rolagem">
        <table>
          <thead><tr><th>Quando</th><th>Origem</th><th>Texto</th><th>Decisão</th><th>Risco</th></tr></thead>
          <tbody>
            {historico.map((h) => (
              <tr key={h.trace_id}>
                <td>{new Date(h.quando).toLocaleString("pt-BR")}</td>
                <td>{h.source_type}</td>
                <td className="trecho">{h.trecho}</td>
                <td><span className={`selo s-${h.decision}`}>{ROTULO[h.decision]}</span></td>
                <td>{(h.risk_score * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
