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
import uuid
from collections import Counter
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
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


def create_app(model_path: str | Path | None = None) -> FastAPI:
    """Fábrica de app: facilita testar com um modelo temporário."""
    app = FastAPI(title="PromptShield 2.0", version=__version__,
                  description="Detecção de prompt injection (PT-BR/EN). Reduz o risco; não o elimina.")
    caminho = Path(model_path or os.getenv("PROMPTSHIELD_MODEL_PATH", "artifacts/model.joblib"))
    app.state.detector = Detector.carregar(caminho) if caminho.exists() else None
    app.state.contagem = Counter()

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

    @app.post("/predict", response_model=AnalyzeResponse)
    def predict(req: AnalyzeRequest):
        d = _detector()
        return _responder(d, req, d.analisar([req.text])[0])

    @app.post("/batch", response_model=list[AnalyzeResponse])
    def batch(req: BatchRequest):
        d = _detector()
        resultados = d.analisar([i.text for i in req.items])
        return [_responder(d, item, r) for item, r in zip(req.items, resultados)]

    @app.get("/metrics")
    def metrics():
        d = _detector()
        return {"model_version": d.versao,
                "limiares": {"t1_review": d.t1, "t2_block": d.t2},
                "metricas_de_treino": d.metricas,
                "runtime": {"total": sum(app.state.contagem.values()), "por_decisao": dict(app.state.contagem)}}

    return app


app = create_app()
