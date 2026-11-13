const CONJUNTOS = [
  ["validacao", "Validação"],
  ["teste_sintetico_moldes_novos", "Teste (moldes novos)"],
  ["externo_46_frases_escritas_a_mao", "Externo (46 frases)"],
];

/** Mostra as métricas REAIS de treino devolvidas por GET /metrics. Nada é digitado aqui. */
export default function ModelMetrics({ metricas }) {
  if (!metricas) return <p className="vazio">Conecte-se à API para ver as métricas do modelo.</p>;
  const m = metricas.metricas_de_treino;
  return (
    <section className="card">
      <h2>Modelo {metricas.model_version}</h2>
      <p className="nota">
        Limiares: revisar ≥ {metricas.limiares.t1_review.toFixed(3)}, bloquear ≥ {metricas.limiares.t2_block.toFixed(3)}.
        Os dados de treino, validação e teste são sintéticos e não foram revisados por humanos.
      </p>
      <div className="rolagem">
        <table>
          <thead><tr><th>Conjunto</th><th>n</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>FP</th><th>FN</th></tr></thead>
          <tbody>
            {CONJUNTOS.map(([chave, nome]) => m[chave] && (
              <tr key={chave}>
                <td>{nome}</td><td>{m[chave].n}</td><td>{m[chave].precision}</td><td>{m[chave].recall}</td>
                <td>{m[chave].f1}</td><td>{m[chave].roc_auc}</td><td>{m[chave].falsos_positivos}</td><td>{m[chave].falsos_negativos}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="nota">Uso desde que o servidor subiu: {metricas.runtime.total} análises.</p>
    </section>
  );
}
