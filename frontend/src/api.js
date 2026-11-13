// Cliente da API. Traduz erros HTTP em mensagens que o usuário entende.
const MENSAGENS = {
  401: "Chave de API inválida ou ausente.",
  422: "Entrada inválida: o texto não pode ser vazio nem passar de 10.000 caracteres.",
  429: "Muitas requisições. Aguarde um instante e tente de novo.",
  503: "O modelo não está carregado no servidor.",
};

async function chamar(baseUrl, caminho, { metodo = "GET", corpo, chave } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (chave) headers.Authorization = `Bearer ${chave}`;
  let resposta;
  try {
    resposta = await fetch(`${baseUrl}${caminho}`, { method: metodo, headers, body: corpo && JSON.stringify(corpo) });
  } catch {
    throw new Error("Não foi possível conectar à API. Ela está rodando em " + baseUrl + "?");
  }
  if (!resposta.ok) throw new Error(MENSAGENS[resposta.status] || `Erro ${resposta.status} na API.`);
  return resposta.json();
}

export const analisar = (cfg, text, source_type) =>
  chamar(cfg.baseUrl, "/predict", { metodo: "POST", corpo: { text, source_type }, chave: cfg.chave });

export const obterMetricas = (cfg) => chamar(cfg.baseUrl, "/metrics", { chave: cfg.chave });
export const verificarSaude = (cfg) => chamar(cfg.baseUrl, "/health", {});
