"""Experimento Transformer: (a) zero-shot com modelo pré-treinado; (b) fine-tuning.

!! STATUS: ESCRITO, NÃO EXECUTADO. !!
   O ambiente onde este arquivo foi criado não tinha GPU nem acesso ao Hugging Face
   (huggingface.co bloqueado), então nenhum número de Transformer existe ainda.
   Rode em uma máquina com acesso (Colab/Kaggle com GPU serve) e registre os
   resultados reais em artifacts/metrics_transformer.json.

Uso (em ambiente com `pip install torch transformers datasets accelerate`):
    python -m promptshield.transformer_experiment --modo zeroshot
    python -m promptshield.transformer_experiment --modo finetune --epocas 3

Reaproveita os MESMOS splits (sem vazamento) e a MESMA função `avaliar` dos baselines,
para a comparação ser justa.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data_builder import carregar_externo
from .train import RAIZ, avaliar, escolher_limiares

MODELO_BASE = "protectai/deberta-v3-base-prompt-injection-v2"  # citado na especificação da Intelliway


def _scores_zeroshot(textos: list[str], nome_modelo: str) -> np.ndarray:
    """Probabilidade da classe 'ataque' segundo o modelo pré-treinado (sem treinar nada)."""
    from transformers import pipeline  # import tardio: só exige a lib quem for rodar
    clf = pipeline("text-classification", model=nome_modelo, truncation=True, max_length=512, top_k=None)
    saida = clf(textos, batch_size=16)
    # Cada item é uma lista [{label, score}, ...]; pegamos o rótulo de injeção.
    return np.array([next(x["score"] for x in item if x["label"].upper().startswith("INJ")) for item in saida])


def _scores_finetune(tr: pd.DataFrame, dfs: dict[str, pd.DataFrame], epocas: int, nome_modelo: str) -> dict[str, np.ndarray]:
    """Fine-tuning completo (cabeça + encoder) com Trainer. Requer GPU para ser prático."""
    import torch
    from datasets import Dataset
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                              Trainer, TrainingArguments)

    tok = AutoTokenizer.from_pretrained(nome_modelo)
    modelo = AutoModelForSequenceClassification.from_pretrained(nome_modelo, num_labels=2,
                                                                ignore_mismatched_sizes=True)

    def tokenizar(lote):  # padding dinâmico fica por conta do Trainer
        return tok(lote["texto"], truncation=True, max_length=256)

    ds_tr = Dataset.from_pandas(tr[["texto", "rotulo"]].rename(columns={"rotulo": "labels"})).map(tokenizar, batched=True)
    args = TrainingArguments(output_dir=str(RAIZ / "artifacts" / "transformer_ckpt"), num_train_epochs=epocas,
                             per_device_train_batch_size=16, learning_rate=2e-5, weight_decay=0.01,
                             seed=42, save_strategy="no", report_to="none", fp16=torch.cuda.is_available())
    Trainer(model=modelo, args=args, train_dataset=ds_tr, tokenizer=tok).train()

    modelo.eval()
    saida = {}
    for nome, d in dfs.items():
        ps = []
        for i in range(0, len(d), 32):
            enc = tok(list(d["texto"].iloc[i:i + 32]), return_tensors="pt", padding=True, truncation=True, max_length=256)
            enc = {k: v.to(modelo.device) for k, v in enc.items()}
            with torch.no_grad():
                ps.append(torch.softmax(modelo(**enc).logits, dim=-1)[:, 1].cpu().numpy())
        saida[nome] = np.concatenate(ps)
    return saida


def main(modo: str, epocas: int) -> dict:
    df = pd.read_csv(RAIZ / "data" / "dataset_v2.csv")
    tr, va, te = (df[df["split"] == s] for s in ("train", "val", "test"))
    ext = carregar_externo(RAIZ / "legacy-sprint1" / "data" / "exemplos_ilustrativos.csv")
    dfs = {"val": va, "teste": te, "externo": ext}

    if modo == "zeroshot":
        scores = {k: _scores_zeroshot(list(d["texto"]), MODELO_BASE) for k, d in dfs.items()}
    else:
        scores = _scores_finetune(tr, dfs, epocas, MODELO_BASE)

    t1, t2 = escolher_limiares(va["rotulo"].to_numpy(), scores["val"])  # limiares SÓ na validação
    rel = {"modo": modo, "modelo_base": MODELO_BASE, "limiares": {"t1_review": t1, "t2_block": t2},
           **{k: avaliar(d, scores[k], t1, t2) for k, d in dfs.items()}}
    (RAIZ / "artifacts" / f"metrics_transformer_{modo}.json").write_text(
        json.dumps(rel, indent=2, ensure_ascii=False), encoding="utf-8")
    return rel


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=["zeroshot", "finetune"], required=True)
    ap.add_argument("--epocas", type=int, default=3)
    a = ap.parse_args()
    print(json.dumps(main(a.modo, a.epocas), indent=2, ensure_ascii=False))
