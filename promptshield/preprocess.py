"""Pré-processamento de texto ANTES de qualquer modelo.

Por que isso existe?
    Um atacante pode alterar a forma do texto sem alterar o significado, para
    escapar de um detector: tirar acentos, esconder caracteres invisíveis no meio
    das palavras, ou codificar a instrução em Base64. Normalizar tudo para uma
    forma canônica faz o modelo enxergar o mesmo texto nos três casos.

Ideia de entrevista: "normalização é a primeira linha de defesa contra evasão;
o modelo só vê a forma canônica".
"""
from __future__ import annotations

import base64
import re
import unicodedata

# Caracteres de largura zero e "hífen suave": invisíveis na tela, mas quebram
# palavras para o tokenizador (ex.: "ig\u200bnore" parece "ignore" para humanos).
_INVISIVEIS = dict.fromkeys(
    map(ord, "\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00ad"), None
)

# Sequências longas só com caracteres do alfabeto Base64 são candidatas a payload.
_BASE64 = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")


def _decodificar_base64(texto: str) -> list[str]:
    """Tenta decodificar trechos Base64 e devolve só os que viram texto legível."""
    achados: list[str] = []
    for token in _BASE64.findall(texto):
        try:
            # validate=True rejeita lixo; o padding "=" é completado se faltar.
            bruto = base64.b64decode(token + "=" * (-len(token) % 4), validate=True)
            decodificado = bruto.decode("utf-8")
        except Exception:  # noqa: BLE001 - qualquer falha = não era Base64 útil
            continue
        legivel = all(c.isprintable() or c.isspace() for c in decodificado)
        if legivel and len(decodificado) >= 8:
            achados.append(decodificado)
    return achados


def normalize(texto: str) -> str:
    """Devolve a forma canônica do texto (minúsculo, sem acento, sem invisíveis).

    Ordem importa: Base64 diferencia maiúsculas de minúsculas, então decodificamos
    ANTES de converter para minúsculas.
    """
    texto = texto.translate(_INVISIVEIS)
    decodificados = _decodificar_base64(texto)
    if decodificados:
        # Mantemos o original e ANEXAMOS o decodificado: o modelo vê os dois.
        texto = texto + " " + " ".join(decodificados)
    texto = texto.lower()
    # NFKD separa a letra do acento; depois descartamos os acentos (categoria "Mn").
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()
