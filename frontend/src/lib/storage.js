// Histórico guardado SÓ no navegador (localStorage). Nada disso vai para um servidor.
const CHAVE = "promptshield.historico.v1";
const LIMITE = 200;

export function carregarHistorico() {
  try {
    const bruto = localStorage.getItem(CHAVE);
    return bruto ? JSON.parse(bruto) : [];
  } catch {
    return []; // storage bloqueado ou JSON corrompido: começa vazio
  }
}

export function salvarHistorico(itens) {
  try {
    localStorage.setItem(CHAVE, JSON.stringify(itens.slice(0, LIMITE)));
  } catch {
    /* sem espaço ou bloqueado: o app continua funcionando em memória */
  }
}
