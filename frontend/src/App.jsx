import { useCallback, useEffect, useState } from "react";
import { analisar, obterMetricas } from "./api.js";
import Dashboard from "./components/Dashboard.jsx";
import HistoryTable from "./components/HistoryTable.jsx";
import ModelMetrics from "./components/ModelMetrics.jsx";
import ResultCard from "./components/ResultCard.jsx";
import { carregarHistorico, salvarHistorico } from "./lib/storage.js";

const ORIGENS = ["USER", "EMAIL", "WEB", "DOCUMENT", "RAG", "IMAGE_TEXT", "AUDIO_TRANSCRIPT", "OTHER"];
const ABAS = [["analisar", "Analisar"], ["historico", "Histórico"], ["dashboard", "Dashboard"], ["modelo", "Modelo"]];

export default function App() {
  const [aba, setAba] = useState("analisar");
  const [baseUrl, setBaseUrl] = useState(import.meta.env.VITE_API_URL || "http://localhost:8000");
  const [chave, setChave] = useState(""); // só em memória: nunca é gravada no navegador
  const [texto, setTexto] = useState("");
  const [origem, setOrigem] = useState("USER");
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [historico, setHistorico] = useState(carregarHistorico);
  const [metricas, setMetricas] = useState(null);

  const cfg = { baseUrl, chave };

  const buscarMetricas = useCallback(async () => {
    try { setMetricas(await obterMetricas({ baseUrl, chave })); } catch { setMetricas(null); }
  }, [baseUrl, chave]);

  useEffect(() => { salvarHistorico(historico); }, [historico]);

  async function aoAnalisar(e) {
    e.preventDefault();
    setErro(""); setCarregando(true);
    try {
      const r = await analisar(cfg, texto, origem);
      setResultado(r);
      setHistorico((h) => [{ ...r, source_type: origem, quando: Date.now(), trecho: texto.slice(0, 140) }, ...h]);
      buscarMetricas(); // atualiza limiares para desenhar as marcas na barra
    } catch (err) {
      setResultado(null); setErro(err.message);
    } finally { setCarregando(false); }
  }

  return (
    <main>
      <header>
        <h1>PromptShield 2.0</h1>
        <p>Detecção de prompt injection em português e inglês.</p>
        <details>
          <summary>Conexão com a API</summary>
          <label>URL <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} /></label>
          <label>Chave de API (opcional, fica só na memória)
            <input type="password" value={chave} autoComplete="off" onChange={(e) => setChave(e.target.value)} />
          </label>
        </details>
      </header>

      <nav role="tablist">
        {ABAS.map(([id, nome]) => (
          <button key={id} role="tab" aria-selected={aba === id} className={aba === id ? "ativa" : ""}
                  onClick={() => { setAba(id); if (id === "modelo") buscarMetricas(); }}>{nome}</button>
        ))}
      </nav>

      {aba === "analisar" && (
        <>
          <form className="card" onSubmit={aoAnalisar}>
            <label>Texto a analisar
              <textarea rows={6} value={texto} maxLength={10000} onChange={(e) => setTexto(e.target.value)}
                        placeholder="Cole um e-mail, trecho de documento, mensagem de usuário..." />
            </label>
            <div className="linha entre">
              <label>Origem
                <select value={origem} onChange={(e) => setOrigem(e.target.value)}>
                  {ORIGENS.map((o) => <option key={o}>{o}</option>)}
                </select>
              </label>
              <button disabled={carregando || !texto.trim()}>{carregando ? "Analisando..." : "Analisar"}</button>
            </div>
          </form>
          {erro && <p className="erro" role="alert">{erro}</p>}
          <ResultCard resultado={resultado} limiares={metricas?.limiares} />
        </>
      )}
      {aba === "historico" && <HistoryTable historico={historico} aoLimpar={() => setHistorico([])} />}
      {aba === "dashboard" && <Dashboard historico={historico} />}
      {aba === "modelo" && <ModelMetrics metricas={metricas} />}
      <footer>Este detector reduz o risco, não o elimina. Veja as limitações no README.</footer>
    </main>
  );
}
