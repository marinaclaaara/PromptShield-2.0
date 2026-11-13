"""API FastAPI do PromptShield 2.0.

Endpoints: POST /predict, POST /batch, GET /health, GET /metrics
Documentação OpenAPI automática em /docs.

Decisões de segurança (defesa em camadas - o classificador NÃO é a única barreira):
  * o texto analisado é tratado só como DADO: nunca é executado nem enviado a um LLM;
  * entrada validada (tamanho máximo, não vazio, lote limitado);
  * o log guarda trace_id, decisão, score e um HASH do texto, nunca o texto bruto
    (evita gravar dados pessoais ou o próprio payload malicioso nos logs);
  * erros não vazam detalhes internos.
"""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
import time
import uuid
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from . import __version__
from .detector import Detector

log = logging.getLogger("promptshield")
# Sem isto, logs INFO de uma biblioteca/app não aparecem (o nível padrão é WARNING).
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
    log.propagate = False

MAX_CHARS = 10_000   # limite por texto
MAX_BATCH = 100      # itens por requisição em lote

SourceType = Literal["USER", "EMAIL", "WEB", "DOCUMENT", "RAG", "IMAGE_TEXT", "AUDIO_TRANSCRIPT",
                     "CONNECTOR", "TOOL_OUTPUT", "IOT_MESSAGE", "EXTERNAL_CONTENT", "OTHER"]


class AnalyzeRequest(BaseModel):
    text: str = Field(..., max_length=MAX_CHARS, description="Conteúdo a analisar.")
    source_type: SourceType = "USER"
    language: str | None = Field(None, description="Opcional, ex.: pt-BR.")

    @field_validator("text")
    @classmethod
    def _nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text não pode ser vazio")
        return v


class BatchRequest(BaseModel):
    items: list[AnalyzeRequest] = Field(..., min_length=1, max_length=MAX_BATCH)


class AnalyzeResponse(BaseModel):
    decision: Literal["ALLOW", "REVIEW", "BLOCK"]
    risk_score: float
    reason_codes: list[str]
    trace_id: str
    model_version: str


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def create_app(model_path: str | Path | None = None, api_keys: set[str] | None = None,
               rate_limit_per_min: int | None = None) -> FastAPI:
    """Fábrica de app: facilita testar com modelo, chaves e limite customizados.

    Autenticação: se houver chaves (parâmetro ou env PROMPTSHIELD_API_KEYS, separadas por
    vírgula), /predict, /batch e /metrics exigem `Authorization: Bearer <chave>`.
    Sem nenhuma chave configurada a API fica ABERTA (útil em dev) e avisa no log.
    Rate limit: janela deslizante de 60 s por chave (ou IP), em MEMÓRIA de um processo.
    """
    app = FastAPI(title="PromptShield 2.0", version=__version__,
                  description="Detecção de prompt injection (PT-BR/EN). Reduz o risco; não o elimina.")
    caminho = Path(model_path or os.getenv("PROMPTSHIELD_MODEL_PATH", "artifacts/model.joblib"))
    app.state.detector = Detector.carregar(caminho) if caminho.exists() else None
    app.state.contagem = Counter()

    chaves = api_keys if api_keys is not None else {
        k.strip() for k in os.getenv("PROMPTSHIELD_API_KEYS", "").split(",") if k.strip()}
    limite = rate_limit_per_min if rate_limit_per_min is not None else int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
    janelas: dict[str, deque] = defaultdict(deque)
    if not chaves:
        log.warning("PROMPTSHIELD_API_KEYS vazio: API SEM autenticação (apenas para desenvolvimento).")

    origens = [o for o in os.getenv("PROMPTSHIELD_CORS_ORIGINS", "http://localhost:5173").split(",") if o]
    app.add_middleware(CORSMiddleware, allow_origins=origens, allow_methods=["GET", "POST"],
                       allow_headers=["Authorization", "Content-Type"])

    def proteger(request: Request, authorization: str | None = Header(default=None)) -> None:
        """Dependência: 401 sem chave válida; 429 se passar do limite por minuto."""
        identidade = request.client.host if request.client else "desconhecido"
        if chaves:
            esquema, _, token = (authorization or "").partition(" ")
            # compare_digest evita ataque de temporização na comparação das chaves
            if esquema.lower() != "bearer" or not any(secrets.compare_digest(token, k) for k in chaves):
                raise HTTPException(status_code=401, detail="Credenciais inválidas.",
                                    headers={"WWW-Authenticate": "Bearer"})
            identidade = "key:" + hashlib.sha256(token.encode()).hexdigest()[:8]
        agora = time.monotonic()
        fila = janelas[identidade]
        while fila and agora - fila[0] > 60:
            fila.popleft()
        if len(fila) >= limite:
            raise HTTPException(status_code=429, detail="Limite de requisições excedido.",
                                headers={"Retry-After": str(max(1, int(60 - (agora - fila[0]))))})
        fila.append(agora)

    def _detector() -> Detector:
        if app.state.detector is None:
            raise HTTPException(status_code=503, detail="Modelo não carregado.")
        return app.state.detector

    def _responder(d: Detector, req: AnalyzeRequest, r: dict) -> AnalyzeResponse:
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        app.state.contagem[r["decision"]] += 1
        log.info("trace=%s decisao=%s score=%.4f origem=%s tam=%d hash=%s",
                 trace_id, r["decision"], r["risk_score"], req.source_type, len(req.text), _hash(req.text))
        return AnalyzeResponse(**r, trace_id=trace_id, model_version=d.versao)

    @app.get("/health")
    def health():
        ok = app.state.detector is not None
        return {"status": "ok" if ok else "degraded", "model_loaded": ok,
                "model_version": app.state.detector.versao if ok else None}

    @app.post("/predict", response_model=AnalyzeResponse, dependencies=[Depends(proteger)])
    def predict(req: AnalyzeRequest):
        d = _detector()
        return _responder(d, req, d.analisar([req.text])[0])

    @app.post("/batch", response_model=list[AnalyzeResponse], dependencies=[Depends(proteger)])
    def batch(req: BatchRequest):
        d = _detector()
        resultados = d.analisar([i.text for i in req.items])
        return [_responder(d, item, r) for item, r in zip(req.items, resultados, strict=True)]

    @app.get("/metrics", dependencies=[Depends(proteger)])
    def metrics():
        d = _detector()
        return {"model_version": d.versao,
                "limiares": {"t1_review": d.t1, "t2_block": d.t2},
                "metricas_de_treino": d.metricas,
                "runtime": {"total": sum(app.state.contagem.values()), "por_decisao": dict(app.state.contagem)}}

    return app


app = create_app()
