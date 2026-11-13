from promptshield.data_builder import carregar_externo, construir_dataset, verificar_vazamento
from promptshield.preprocess import normalize
from tests.conftest import LEGACY


def _df():
    return construir_dataset(carregar_externo(LEGACY), seed=1, cap_por_molde=60)


def test_tamanho_minimo_e_idiomas():
    df = _df()
    assert len(df) >= 2000
    assert set(df["idioma"]) == {"pt", "en"}


def test_sem_vazamento_entre_splits():
    assert all(v == 0 for v in verificar_vazamento(_df()).values())


def test_sem_duplicatas_normalizadas():
    df = _df()
    assert df["texto"].map(normalize).is_unique


def test_externo_nunca_entra_no_treino():
    df = _df()
    ext = set(carregar_externo(LEGACY)["texto"].map(normalize))
    assert not (set(df["texto"].map(normalize)) & ext)


def test_todos_os_splits_tem_as_duas_classes_e_hard_negatives():
    df = _df()
    for s in ("train", "val", "test"):
        parte = df[df["split"] == s]
        assert set(parte["rotulo"]) == {0, 1}
        assert parte["hard_negative"].sum() > 0


def test_origem_marcada_como_sintetica_e_nao_revisada():
    df = _df()
    assert (df["origem_dado"] == "sintetico_template").all()
    assert not df["revisado_humano"].any()
