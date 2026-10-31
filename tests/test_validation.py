import pytest

from sunat_ubl import validar_dni, validar_ruc, validar_serie


@pytest.mark.parametrize("ruc", ["20100070970", "20512345671", "20999999990"])
def test_ruc_valido(ruc):
    assert validar_ruc(ruc)


@pytest.mark.parametrize(
    "ruc",
    [
        "20100070971",  # dígito verificador incorrecto
        "2010007097",  # 10 dígitos
        "201000709700",  # 12 dígitos
        "30100070970",  # prefijo inválido
        "20100A70970",  # no numérico
        "",
    ],
)
def test_ruc_invalido(ruc):
    assert not validar_ruc(ruc)


def test_dni():
    assert validar_dni("12345678")
    assert not validar_dni("1234567")
    assert not validar_dni("1234567A")


@pytest.mark.parametrize(
    ("serie", "tipo", "esperado"),
    [
        ("F001", "01", True),
        ("FZZ9", "01", True),
        ("B001", "03", True),
        ("B001", "01", False),
        ("F001", "03", False),
        ("f001", "01", False),
        ("F01", "01", False),
        ("F01a", "01", False),
    ],
)
def test_series(serie, tipo, esperado):
    assert validar_serie(serie, tipo) is esperado
