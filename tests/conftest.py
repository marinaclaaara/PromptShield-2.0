"""Fixture: treina um modelo pequeno UMA vez por sessão de testes, em pasta temporária."""
from pathlib import Path

import pytest

from promptshield import train

RAIZ = Path(__file__).resolve().parent.parent
LEGACY = RAIZ / "legacy-sprint1" / "data" / "exemplos_ilustrativos.csv"


@pytest.fixture(scope="session")
def relatorio_e_modelo(tmp_path_factory):
    saida = tmp_path_factory.mktemp("artefatos")
    rel = train.main(saida, LEGACY, cap_por_molde=20)  # pequeno = teste rápido
    return rel, saida / "model.joblib"
