from datetime import date
from decimal import Decimal

import pytest

from sunat_ubl import Cliente, Comprobante, Emisor, Linea

EMISOR = Emisor(ruc="20999999990", razon_social="SERVICIOS DEMO PERU SAC")
CLIENTE = Cliente(tipo_doc="6", numero="20512345671", razon_social="CLIENTE DE PRUEBA SAC")


def comprobante(lineas):
    return Comprobante(
        tipo="01",
        serie="F001",
        numero=1,
        fecha=date(2026, 10, 30),
        emisor=EMISOR,
        cliente=CLIENTE,
        lineas=lineas,
    )


def test_linea_gravada_calcula_igv():
    linea = Linea("Servicio", cantidad=2, valor_unitario="100.00")
    assert linea.subtotal == Decimal("200.00")
    assert linea.igv == Decimal("36.00")
    assert linea.total == Decimal("236.00")


def test_linea_exonerada_no_cobra_igv():
    linea = Linea("Servicio exonerado", cantidad=1, valor_unitario="50.00", tipo_afectacion="20")
    assert linea.subtotal == Decimal("50.00")
    assert linea.igv == Decimal("0.00")


def test_precio_con_igv_cuadra_al_centimo():
    linea = Linea.desde_precio_con_igv("Soporte", cantidad=1, precio_con_igv=100)
    assert linea.subtotal == Decimal("84.75")
    assert linea.igv == Decimal("15.25")
    assert linea.total == Decimal("100.00")


def test_precio_con_igv_varias_unidades():
    linea = Linea.desde_precio_con_igv("Soporte", cantidad=3, precio_con_igv="33.90")
    assert linea.total == Decimal("101.70")
    assert linea.subtotal + linea.igv == linea.total


def test_totales_del_comprobante():
    doc = comprobante(
        [
            Linea("A", cantidad=2, valor_unitario="100.00"),
            Linea.desde_precio_con_igv("B", cantidad=1, precio_con_igv=118),
            Linea("C", cantidad=1, valor_unitario="50.00", tipo_afectacion="20"),
        ]
    )
    assert doc.valor_venta == Decimal("350.00")
    assert doc.total_igv == Decimal("54.00")
    assert doc.importe_total == Decimal("404.00")
    assert doc.total_gravado == Decimal("300.00")
    assert doc.total_exonerado == Decimal("50.00")


def test_subtotales_por_tributo():
    doc = comprobante(
        [
            Linea("A", cantidad=1, valor_unitario="100.00"),
            Linea("B", cantidad=1, valor_unitario="50.00", tipo_afectacion="20"),
        ]
    )
    grupos = doc.subtotales_impuestos()
    assert [g["tributo"] for g in grupos] == ["1000", "9997"]
    assert grupos[0]["base"] == Decimal("100.00")
    assert grupos[0]["importe"] == Decimal("18.00")
    assert grupos[1]["base"] == Decimal("50.00")
    assert grupos[1]["motivo"] == "20"


def test_nombre_archivo_sunat():
    assert comprobante([Linea("A", 1, "1")]).nombre_archivo == "20999999990-01-F001-1"


@pytest.mark.parametrize(
    ("kwargs", "mensaje"),
    [
        ({"serie": "B001"}, "Serie inválida"),
        ({"numero": 0}, "Número de comprobante inválido"),
        ({"tipo": "07"}, "no soportado"),
        ({"lineas": []}, "al menos una línea"),
        ({"moneda": "soles"}, "Moneda inválida"),
    ],
)
def test_validaciones_del_comprobante(kwargs, mensaje):
    datos = dict(
        tipo="01",
        serie="F001",
        numero=1,
        fecha=date(2026, 10, 30),
        emisor=EMISOR,
        cliente=CLIENTE,
        lineas=[Linea("A", 1, "1")],
    )
    datos.update(kwargs)
    with pytest.raises(ValueError, match=mensaje):
        Comprobante(**datos)


def test_validacion_de_ruc_del_emisor():
    with pytest.raises(ValueError, match="RUC del emisor inválido"):
        Emisor(ruc="20100070971", razon_social="X")


def test_afectacion_desconocida():
    with pytest.raises(ValueError, match="no soportado"):
        Linea("A", 1, "1", tipo_afectacion="99")
