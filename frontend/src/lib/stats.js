// Funções PURAS (sem React) que calculam as estatísticas do dashboard.
// Ficam separadas para poderem ser testadas sem navegador (node --test).

export const DECISOES = ["ALLOW", "REVIEW", "BLOCK"];

/** Conta quantas análises caíram em cada decisão. */
export function contarDecisoes(historico) {
  const contagem = { ALLOW: 0, REVIEW: 0, BLOCK: 0 };
  for (const item of historico) if (item.decision in contagem) contagem[item.decision] += 1;
  return contagem;
}

/** Histograma do risco em `faixas` intervalos iguais de 0 a 1 (score 1.0 entra na última faixa). */
export function histogramaRisco(historico, faixas = 10) {
  const bins = new Array(faixas).fill(0);
  for (const item of historico) {
    const s = Math.min(Math.max(item.risk_score, 0), 1);
    bins[Math.min(Math.floor(s * faixas), faixas - 1)] += 1;
  }
  return bins;
}

/** Resumo geral usado nos cartões do topo. */
export function resumir(historico) {
  const total = historico.length;
  const contagem = contarDecisoes(historico);
  const mediaRisco = total ? historico.reduce((a, i) => a + i.risk_score, 0) / total : 0;
  const suspeitos = contagem.REVIEW + contagem.BLOCK;
  return { total, contagem, mediaRisco, taxaSuspeitos: total ? suspeitos / total : 0 };
}

export function formatarPercentual(x) {
  return `${(x * 100).toFixed(1).replace(".", ",")}%`;
}
