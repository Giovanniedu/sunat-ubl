from datetime import date, time
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from sunat_ubl import Cliente, Comprobante, Emisor, Linea, a_xml, guardar
from sunat_ubl.generator import NS_CAC, NS_CBC, NS_INVOICE


def _local(tag):
    return tag.rsplit("}", 1)[-1]


@pytest.fixture
def factura():
    return Comprobante(
        tipo="01",
        serie="F001",
        numero=1,
        fecha=date(2026, 10, 30),
        hora=time(15, 42, 10),
        emisor=Emisor(
            ruc="20999999990",
            razon_social="SERVICIOS DEMO PERU SAC",
            nombre_comercial="Demo Perú",
            direccion="AV. SIEMPRE VIVA 123",
            ubigeo="150101",
        ),
        cliente=Cliente(tipo_doc="6", numero="20512345671", razon_social="CLIENTE DE PRUEBA SAC"),
        lineas=[
            Linea("A", cantidad=2, valor_unitario="100.00", unidad="ZZ"),
            Linea.desde_precio_con_igv("B", cantidad=1, precio_con_igv=118, unidad="ZZ"),
            Linea("C", cantidad=1, valor_unitario="50.00", tipo_afectacion="20", unidad="ZZ"),
        ],
    )


def test_raiz_y_namespaces(factura):
    raiz = ET.fromstring(a_xml(factura))
    assert raiz.tag == f"{{{NS_INVOICE}}}Invoice"


def test_orden_de_elementos_exigido_por_sunat(factura):
    raiz = ET.fromstring(a_xml(factura))
    orden = [_local(hijo.tag) for hijo in raiz]
    assert orden == [
        "UBLExtensions",
        "UBLVersionID",
        "CustomizationID",
        "ID",
        "IssueDate",
        "IssueTime",
        "InvoiceTypeCode",
        "DocumentCurrencyCode",
        "LineCountNumeric",
        "AccountingSupplierParty",
        "AccountingCustomerParty",
        "TaxTotal",
        "LegalMonetaryTotal",
        "InvoiceLine",
        "InvoiceLine",
        "InvoiceLine",
    ]


def test_cabecera(factura):
    raiz = ET.fromstring(a_xml(factura))
    assert raiz.findtext(f"{{{NS_CBC}}}UBLVersionID") == "2.1"
    assert raiz.findtext(f"{{{NS_CBC}}}CustomizationID") == "2.0"
    assert raiz.findtext(f"{{{NS_CBC}}}ID") == "F001-1"
    assert raiz.findtext(f"{{{NS_CBC}}}IssueDate") == "2026-10-30"
    assert raiz.findtext(f"{{{NS_CBC}}}IssueTime") == "15:42:10"
    tipo = raiz.find(f"{{{NS_CBC}}}InvoiceTypeCode")
    assert tipo.text == "01"
    assert tipo.get("listID") == "0101"
    assert raiz.findtext(f"{{{NS_CBC}}}DocumentCurrencyCode") == "PEN"
    assert raiz.findtext(f"{{{NS_CBC}}}LineCountNumeric") == "3"


def test_totales_del_xml(factura):
    raiz = ET.fromstring(a_xml(factura))
    total = raiz.find(f"{{{NS_CAC}}}LegalMonetaryTotal")
    assert total.findtext(f"{{{NS_CBC}}}LineExtensionAmount") == "350.00"
    assert total.findtext(f"{{{NS_CBC}}}TaxInclusiveAmount") == "404.00"
    assert total.findtext(f"{{{NS_CBC}}}PayableAmount") == "404.00"

    impuestos = raiz.find(f"{{{NS_CAC}}}TaxTotal")
    assert impuestos.findtext(f"{{{NS_CBC}}}TaxAmount") == "54.00"
    subtotales = impuestos.findall(f"{{{NS_CAC}}}TaxSubtotal")
    assert len(subtotales) == 2
    assert subtotales[0].findtext(f"{{{NS_CBC}}}TaxableAmount") == "300.00"
    assert subtotales[1].findtext(f"{{{NS_CBC}}}TaxableAmount") == "50.00"


def test_emisor_con_ruc_y_ubigeo(factura):
    raiz = ET.fromstring(a_xml(factura))
    proveedor = raiz.find(f"{{{NS_CAC}}}AccountingSupplierParty/{{{NS_CAC}}}Party")
    identificacion = proveedor.find(f"{{{NS_CAC}}}PartyIdentification/{{{NS_CBC}}}ID")
    assert identificacion.text == "20999999990"
    assert identificacion.get("schemeID") == "6"
    assert proveedor.findtext(f"{{{NS_CAC}}}PartyName/{{{NS_CBC}}}Name") == "Demo Perú"
    ubigeo = proveedor.find(
        f"{{{NS_CAC}}}PartyLegalEntity/{{{NS_CAC}}}RegistrationAddress/{{{NS_CBC}}}ID"
    )
    assert ubigeo.text == "150101"


def test_linea_exonerada_lleva_motivo(factura):
    raiz = ET.fromstring(a_xml(factura))
    lineas = raiz.findall(f"{{{NS_CAC}}}InvoiceLine")
    categoria = lineas[2].find(
        f"{{{NS_CAC}}}TaxTotal/{{{NS_CAC}}}TaxSubtotal/{{{NS_CAC}}}TaxCategory"
    )
    assert categoria.findtext(f"{{{NS_CBC}}}ID") == "E"
    assert categoria.findtext(f"{{{NS_CBC}}}TaxExemptionReasonCode") == "20"
    assert lineas[2].findtext(f"{{{NS_CAC}}}TaxTotal/{{{NS_CBC}}}TaxAmount") == "0.00"


def test_precio_unitario_con_igv_en_la_linea(factura):
    raiz = ET.fromstring(a_xml(factura))
    linea = raiz.findall(f"{{{NS_CAC}}}InvoiceLine")[1]
    precio = linea.find(
        f"{{{NS_CAC}}}PricingReference/{{{NS_CAC}}}AlternativeConditionPrice/{{{NS_CBC}}}PriceAmount"
    )
    assert precio.text == "118.00"
    valor = linea.find(f"{{{NS_CAC}}}Price/{{{NS_CBC}}}PriceAmount")
    assert valor.text == "100.00"
    base = linea.find(f"{{{NS_CAC}}}Price/{{{NS_CBC}}}BaseQuantity")
    assert base.text == "1"


def test_guardar_escribe_el_nombre_de_sunat(factura, tmp_path):
    ruta = guardar(factura, directorio=str(tmp_path))
    assert Path(ruta).name == "20999999990-01-F001-1.xml"
    assert Path(ruta).read_text(encoding="utf-8").startswith("<?xml version='1.0' encoding='utf-8'?>")


def test_sin_indentar_produce_una_sola_linea(factura):
    cuerpo = a_xml(factura, indentar=False).split(b"?>", 1)[1]
    assert b"\n" not in cuerpo.strip()


def test_boleta_con_dni():
    boleta = Comprobante(
        tipo="03",
        serie="B001",
        numero=7,
        fecha=date(2026, 10, 30),
        emisor=Emisor(ruc="20999999990", razon_social="SERVICIOS DEMO PERU SAC"),
        cliente=Cliente(tipo_doc="1", numero="12345678", razon_social="JUAN PEREZ"),
        lineas=[Linea("Producto", cantidad=1, valor_unitario="10.00")],
    )
    raiz = ET.fromstring(a_xml(boleta))
    assert raiz.findtext(f"{{{NS_CBC}}}InvoiceTypeCode") == "03"
    cliente = raiz.find(f"{{{NS_CAC}}}AccountingCustomerParty/{{{NS_CAC}}}Party")
    documento = cliente.find(f"{{{NS_CAC}}}PartyIdentification/{{{NS_CBC}}}ID")
    assert documento.text == "12345678"
    assert documento.get("schemeID") == "1"
