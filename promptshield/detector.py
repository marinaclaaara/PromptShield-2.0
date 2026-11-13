"""Camada de inferência: carrega o modelo salvo e converte score em decisão."""
from __future__ import annotations

from pathlib import Path

import joblib


class Detector:
    """Envolve o Pipeline treinado + limiares + versão.

    Separar isso da API permite testar a lógica de decisão sem subir servidor HTTP.
    """

    def __init__(self, pack: dict):
        self._pipe = pack["pipeline"]
        self.t1: float = pack["t1"]      # abaixo disso: ALLOW
        self.t2: float = pack["t2"]      # a partir disso: BLOCK
        self.versao: str = pack["versao"]
        self.metricas: dict = pack.get("metricas", {})

    @classmethod
    def carregar(cls, caminho: str | Path) -> Detector:
        return cls(joblib.load(caminho))

    def decidir(self, score: float) -> tuple[str, list[str]]:
        """ALLOW < t1 <= REVIEW < t2 <= BLOCK  (+ códigos de motivo p/ auditoria)."""
        if score >= self.t2:
            return "BLOCK", ["HIGH_RISK_SCORE"]
        if score >= self.t1:
            return "REVIEW", ["MEDIUM_RISK_SCORE"]
        return "ALLOW", []

    def analisar(self, textos: list[str]) -> list[dict]:
        # predict_proba aceita lote: mais rápido que chamar um a um.
        scores = self._pipe.predict_proba(textos)[:, 1]
        saida = []
        for s in scores:
            decisao, motivos = self.decidir(float(s))
            saida.append({"decision": decisao, "risk_score": round(float(s), 4),
                          "reason_codes": motivos})
        return saida
