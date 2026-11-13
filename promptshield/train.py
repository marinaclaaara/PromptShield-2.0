"""Treina e compara os baselines clássicos; salva o melhor modelo + métricas reais.

Uso:
    python -m promptshield.train

Modelos comparados (todos sobre TF-IDF de palavras + bigramas, com normalização):
    1. Regressão Logística
    2. Linear SVM (calibrado para devolver probabilidade)

Os modelos Transformer (pré-treinado e com fine-tuning) estão em
`promptshield/transformer_experiment.py`, mas NÃO foram executados no ambiente
onde este código foi escrito (sem GPU e sem acesso ao Hugging Face).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score,
                             recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from . import __version__
from .data_builder import carregar_externo, construir_dataset, verificar_vazamento
from .preprocess import normalize

SEED = 42
RAIZ = Path(__file__).resolve().parent.parent


def montar_modelos() -> dict[str, Pipeline]:
    """Cada Pipeline = TF-IDF + classificador. Treinar em Pipeline garante que o
    vocabulário do TF-IDF é aprendido SÓ no treino (sem vazar o teste)."""
    def tfidf() -> TfidfVectorizer:
        # `preprocessor=normalize` aplica nossa normalização dentro do vetorizador,
        # então ela viaja junto com o modelo salvo (a API usa exatamente a mesma).
        return TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2),
                               sublinear_tf=True, min_df=2)
    return {
        "tfidf_logreg": Pipeline([
            ("tfidf", tfidf()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)),
        ]),
        "tfidf_linearsvm": Pipeline([
            ("tfidf", tfidf()),
            # LinearSVC não dá probabilidade; CalibratedClassifierCV converte a
            # distância à fronteira em probabilidade (necessária p/ ALLOW/REVIEW/BLOCK).
            ("clf", CalibratedClassifierCV(LinearSVC(class_weight="balanced", random_state=SEED),
                                           cv=3)),
        ]),
    }


def escolher_limiares(y_val: np.ndarray, scores_val: np.ndarray) -> tuple[float, float]:
    """Escolhe (t1, t2) na VALIDAÇÃO.

    t1 (REVIEW): menor limiar que ainda captura >= 98% dos ataques (recall alto).
    t2 (BLOCK):  menor limiar com precisão >= 99% (bloquear só com muita certeza).
    Ver ALLOW < t1 <= REVIEW < t2 <= BLOCK.
    """
    prec, rec, lim = precision_recall_curve(y_val, scores_val)
    prec, rec = prec[:-1], rec[:-1]  # alinha com `lim`
    ok_rec = lim[rec >= 0.98]
    t1 = float(ok_rec.max()) if len(ok_rec) else 0.30
    ok_prec = lim[prec >= 0.99]
    t2 = float(ok_prec.min()) if len(ok_prec) else 0.90
    return min(t1, t2), max(t1, t2)


def avaliar(df: pd.DataFrame, scores: np.ndarray, t1: float, t2: float) -> dict:
    """Todas as métricas pedidas. REVIEW e BLOCK contam como 'ataque previsto'."""
    y = df["rotulo"].to_numpy()
    pred = (scores >= t1).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    hn = (df["hard_negative"].to_numpy() == 1)
    return {
        "n": int(len(df)),
        "accuracy": round(accuracy_score(y, pred), 4),
        "precision": round(precision_score(y, pred, zero_division=0), 4),
        "recall": round(recall_score(y, pred, zero_division=0), 4),
        "f1": round(f1_score(y, pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y, scores), 4),
        "matriz_confusao": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "falsos_positivos": int(fp),
        "falsos_negativos": int(fn),
        # FPR nos hard negatives: dos legítimos que PARECEM ataque, quantos foram marcados?
        "fpr_hard_negatives": {"fp": int((pred[hn] == 1).sum()), "total": int(hn.sum())},
        "distribuicao_decisao": {
            "ALLOW": int((scores < t1).sum()),
            "REVIEW": int(((scores >= t1) & (scores < t2)).sum()),
            "BLOCK": int((scores >= t2).sum()),
        },
    }


def main(saida: Path, legacy_csv: Path, cap_por_molde: int = 60) -> dict:
    saida.mkdir(parents=True, exist_ok=True)

    externo = carregar_externo(legacy_csv)
    df = construir_dataset(externo, seed=SEED, cap_por_molde=cap_por_molde)
    vazamento = verificar_vazamento(df)
    assert all(v == 0 for v in vazamento.values()), f"VAZAMENTO DETECTADO: {vazamento}"

    df.to_csv(RAIZ / "data" / "dataset_v2.csv", index=False)
    dataset_hash = hashlib.sha256(df["texto"].str.cat(sep="\n").encode()).hexdigest()[:10]

    tr, va, te = (df[df["split"] == s] for s in ("train", "val", "test"))
    relatorio = {"dataset": {
        "total": int(len(df)), "por_split": df["split"].value_counts().to_dict(),
        "por_idioma": df["idioma"].value_counts().to_dict(),
        "por_familia": df["familia"].value_counts().to_dict(),
        "ataques": int(df["rotulo"].sum()), "hard_negatives": int(df["hard_negative"].sum()),
        "origem": "100% sintetico_template (NAO revisado por humanos); externo = 46 frases do grupo original",
        "vazamento_verificado": vazamento, "hash": dataset_hash,
    }, "modelos": {}}

    melhor_nome, melhor_f1, melhor_pack = None, -1.0, None
    for nome, pipe in montar_modelos().items():
        pipe.fit(tr["texto"], tr["rotulo"])
        score = lambda d: pipe.predict_proba(d["texto"])[:, 1]  # noqa: E731
        t1, t2 = escolher_limiares(va["rotulo"].to_numpy(), score(va))
        mets = {
            "limiares": {"t1_review": round(t1, 4), "t2_block": round(t2, 4)},
            "validacao": avaliar(va, score(va), t1, t2),
            "teste_sintetico_moldes_novos": avaliar(te, score(te), t1, t2),
            "externo_46_frases_escritas_a_mao": avaliar(externo, score(externo), t1, t2),
        }
        relatorio["modelos"][nome] = mets
        # A escolha do melhor modelo usa SÓ a validação (nunca o teste nem o externo).
        if mets["validacao"]["f1"] > melhor_f1:
            melhor_nome, melhor_f1, melhor_pack = nome, mets["validacao"]["f1"], (pipe, t1, t2)

    pipe, t1, t2 = melhor_pack
    versao = f"{__version__}-{melhor_nome}-{dataset_hash}"
    relatorio["modelo_escolhido"] = {"nome": melhor_nome, "versao": versao,
                                     "criterio": "maior F1 na validacao; empate -> primeiro da lista (o mais simples). test e externo nao participam"}
    joblib.dump({"pipeline": pipe, "t1": t1, "t2": t2, "versao": versao,
                 "metricas": relatorio["modelos"][melhor_nome]}, saida / "model.joblib")
    relatorio["gerado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (saida / "metrics.json").write_text(json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")
    return relatorio


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=RAIZ / "artifacts")
    ap.add_argument("--legacy-csv", type=Path,
                    default=RAIZ / "legacy-sprint1" / "data" / "exemplos_ilustrativos.csv")
    a = ap.parse_args()
    r = main(a.out, a.legacy_csv)
    print(json.dumps({k: r[k] for k in ("dataset", "modelo_escolhido")}, indent=2, ensure_ascii=False))
    for nome, m in r["modelos"].items():
        print(f"\n== {nome}  limiares={m['limiares']}")
        for conj in ("validacao", "teste_sintetico_moldes_novos", "externo_46_frases_escritas_a_mao"):
            x = m[conj]
            print(f"  {conj:<36} n={x['n']:<4} P={x['precision']:.3f} R={x['recall']:.3f} "
                  f"F1={x['f1']:.3f} AUC={x['roc_auc']:.3f} FP={x['falsos_positivos']} FN={x['falsos_negativos']} "
                  f"FPR_hn={x['fpr_hard_negatives']['fp']}/{x['fpr_hard_negatives']['total']}")
