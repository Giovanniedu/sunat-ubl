"""Generación del XML UBL 2.1 que SUNAT acepta en el SEE-SOL."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP

from .catalogs import TRIBUTOS
from .models import Comprobante, Linea, dinero

NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
NS_DS = "http://www.w3.org/2000/09/xmldsig#"

for _prefijo, _uri in (("", NS_INVOICE), ("cac", NS_CAC), ("cbc", NS_CBC), ("ext", NS_EXT), ("ds", NS_DS)):
    ET.register_namespace(_prefijo, _uri)

_AGENCIA_UN = "United Nations Economic Commission for Europe"
_URI_CATALOGO_06 = "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06"
_URI_CATALOGO_16 = "urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16"


def _qns(ns: str, etiqueta: str) -> str:
    return f"{{{ns}}}{etiqueta}"


def _el(parent: ET.Element, ns: str, etiqueta: str, texto: str | None = None, **attrs: str) -> ET.Element:
    elemento = ET.SubElement(parent, _qns(ns, etiqueta))
    for clave, valor in attrs.items():
        elemento.set(clave, str(valor))
    if texto is not None:
        elemento.text = texto
    return elemento


def _monto(valor: Decimal) -> str:
    return f"{dinero(valor):.2f}"


def _numero(valor: Decimal, decimales: int = 10) -> str:
    limite = Decimal(1).scaleb(-decimales)
    texto = format(Decimal(valor).quantize(limite, rounding=ROUND_HALF_UP), "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto or "0"


def _precio(valor: Decimal) -> str:
    """Precios con 2 decimales mínimos, como en los XML de referencia de SUNAT."""
    texto = _numero(valor)
    if "." not in texto:
        return f"{texto}.00"
    entero, decimales = texto.split(".")
    return f"{entero}.{decimales.ljust(2, '0')}"


def _id_documento(parent: ET.Element, tipo_doc: str, numero: str) -> None:
    _el(
        parent,
        NS_CBC,
        "ID",
        numero,
        schemeID=tipo_doc,
        schemeName="Documento de Identidad",
        schemeAgencyName="PE:SUNAT",
        schemeURI=_URI_CATALOGO_06,
    )


def _parte_cliente(comprobante: Comprobante) -> ET.Element:
    parte = ET.Element(_qns(NS_CAC, "Party"))
    identificacion = _el(parte, NS_CAC, "PartyIdentification")
    _id_documento(identificacion, comprobante.cliente.tipo_doc, comprobante.cliente.numero)
    legal = _el(parte, NS_CAC, "PartyLegalEntity")
    _el(legal, NS_CBC, "RegistrationName", comprobante.cliente.razon_social)
    if comprobante.cliente.direccion:
        direccion = _el(legal, NS_CAC, "RegistrationAddress")
        linea_direccion = _el(direccion, NS_CAC, "AddressLine")
        _el(linea_direccion, NS_CBC, "Line", comprobante.cliente.direccion)
    if comprobante.cliente.email:
        contacto = _el(parte, NS_CAC, "Contact")
        _el(contacto, NS_CBC, "ElectronicMail", comprobante.cliente.email)
    return parte


def _parte_emisor(comprobante: Comprobante) -> ET.Element:
    emisor = comprobante.emisor
    parte = ET.Element(_qns(NS_CAC, "Party"))
    identificacion = _el(parte, NS_CAC, "PartyIdentification")
    _id_documento(identificacion, "6", emisor.ruc)
    if emisor.nombre_comercial:
        nombre = _el(parte, NS_CAC, "PartyName")
        _el(nombre, NS_CBC, "Name", emisor.nombre_comercial)
    legal = _el(parte, NS_CAC, "PartyLegalEntity")
    _el(legal, NS_CBC, "RegistrationName", emisor.razon_social)
    _el(
        legal,
        NS_CBC,
        "CompanyID",
        emisor.ruc,
        schemeID="6",
        schemeName="Documento de Identidad",
        schemeAgencyName="PE:SUNAT",
        schemeURI=_URI_CATALOGO_06,
    )
    if emisor.direccion or emisor.ubigeo:
        direccion = _el(legal, NS_CAC, "RegistrationAddress")
        if emisor.ubigeo:
            _el(direccion, NS_CBC, "ID", emisor.ubigeo, schemeName="Ubigeos", schemeAgencyName="PE:INEI")
        if emisor.direccion:
            linea = _el(direccion, NS_CAC, "AddressLine")
            _el(linea, NS_CBC, "Line", emisor.direccion)
        pais = _el(direccion, NS_CAC, "Country")
        _el(
            pais,
            NS_CBC,
            "IdentificationCode",
            "PE",
            listID="ISO 3166-1",
            listAgencyName=_AGENCIA_UN,
            listName="Country",
        )
    return parte


def _categoria_impuesto(parent: ET.Element, categoria: str, porcentaje: Decimal, motivo: str | None, tributo: str) -> None:
    tax_category = _el(parent, NS_CAC, "TaxCategory")
    _el(
        tax_category,
        NS_CBC,
        "ID",
        categoria,
        schemeID="UN/ECE 5305",
        schemeName="Tax Category Identifier",
        schemeAgencyName=_AGENCIA_UN,
    )
    _el(tax_category, NS_CBC, "Percent", _monto(porcentaje))
    if motivo:
        _el(tax_category, NS_CBC, "TaxExemptionReasonCode", motivo)
    tax_scheme = _el(tax_category, NS_CAC, "TaxScheme")
    nombre, tipo = TRIBUTOS[tributo]
    _el(
        tax_scheme,
        NS_CBC,
        "ID",
        tributo,
        schemeID="UN/ECE 5153",
        schemeName="Tax Scheme Identifier",
        schemeAgencyName=_AGENCIA_UN,
    )
    _el(tax_scheme, NS_CBC, "Name", nombre)
    _el(tax_scheme, NS_CBC, "TaxTypeCode", tipo)


def _totales_impuestos(parent: ET.Element, comprobante: Comprobante) -> None:
    moneda = comprobante.moneda
    total = _el(parent, NS_CAC, "TaxTotal")
    _el(total, NS_CBC, "TaxAmount", _monto(comprobante.total_igv), currencyID=moneda)
    for grupo in comprobante.subtotales_impuestos():
        subtotal = _el(total, NS_CAC, "TaxSubtotal")
        _el(subtotal, NS_CBC, "TaxableAmount", _monto(grupo["base"]), currencyID=moneda)
        _el(subtotal, NS_CBC, "TaxAmount", _monto(grupo["importe"]), currencyID=moneda)
        motivo = grupo["motivo"] if grupo["tributo"] != "1000" else None
        _categoria_impuesto(subtotal, grupo["categoria"], grupo["tasa"] * 100, motivo, grupo["tributo"])


def _linea_xml(parent: ET.Element, linea: Linea, posicion: int, moneda: str) -> None:
    afectacion_linea = linea.afectacion
    nodo = _el(parent, NS_CAC, "InvoiceLine")
    _el(nodo, NS_CBC, "ID", str(posicion))
    _el(nodo, NS_CBC, "InvoicedQuantity", _numero(linea.cantidad), unitCode=linea.unidad)
    _el(nodo, NS_CBC, "LineExtensionAmount", _monto(linea.subtotal), currencyID=moneda)

    referencia = _el(nodo, NS_CAC, "PricingReference")
    alternativo = _el(referencia, NS_CAC, "AlternativeConditionPrice")
    _el(alternativo, NS_CBC, "PriceAmount", _precio(linea.precio_con_igv), currencyID=moneda)
    _el(
        alternativo,
        NS_CBC,
        "PriceTypeCode",
        "01",
        listName="Tipo de Precio",
        listAgencyName="PE:SUNAT",
        listURI=_URI_CATALOGO_16,
    )

    total_linea = _el(nodo, NS_CAC, "TaxTotal")
    _el(total_linea, NS_CBC, "TaxAmount", _monto(linea.igv), currencyID=moneda)
    subtotal = _el(total_linea, NS_CAC, "TaxSubtotal")
    _el(subtotal, NS_CBC, "TaxableAmount", _monto(linea.subtotal), currencyID=moneda)
    _el(subtotal, NS_CBC, "TaxAmount", _monto(linea.igv), currencyID=moneda)
    _categoria_impuesto(
        subtotal,
        afectacion_linea.categoria,
        afectacion_linea.tasa * 100,
        linea.tipo_afectacion if afectacion_linea.exenta else None,
        afectacion_linea.tributo,
    )

    item = _el(nodo, NS_CAC, "Item")
    _el(item, NS_CBC, "Description", linea.descripcion)
    if linea.codigo:
        identificacion = _el(item, NS_CAC, "SellersItemIdentification")
        _el(identificacion, NS_CBC, "ID", linea.codigo)

    precio = _el(nodo, NS_CAC, "Price")
    _el(precio, NS_CBC, "PriceAmount", _precio(linea.valor_unitario), currencyID=moneda)
    _el(precio, NS_CBC, "BaseQuantity", "1", unitCode=linea.unidad)


def construir(comprobante: Comprobante) -> ET.Element:
    """Devuelve el elemento raíz <Invoice> listo para serializar."""
    moneda = comprobante.moneda
    raiz = ET.Element(_qns(NS_INVOICE, "Invoice"))

    extensiones = _el(raiz, NS_EXT, "UBLExtensions")
    extension = _el(extensiones, NS_EXT, "UBLExtension")
    _el(extension, NS_EXT, "ExtensionContent")

    _el(raiz, NS_CBC, "UBLVersionID", "2.1")
    _el(raiz, NS_CBC, "CustomizationID", "2.0")
    _el(raiz, NS_CBC, "ID", comprobante.identificador)
    _el(raiz, NS_CBC, "IssueDate", comprobante.fecha.isoformat())
    if comprobante.hora is not None:
        _el(raiz, NS_CBC, "IssueTime", comprobante.hora.strftime("%H:%M:%S"))
    _el(raiz, NS_CBC, "InvoiceTypeCode", comprobante.tipo, listID="0101")
    if comprobante.observacion:
        _el(raiz, NS_CBC, "Note", comprobante.observacion)
    _el(raiz, NS_CBC, "DocumentCurrencyCode", moneda)
    _el(raiz, NS_CBC, "LineCountNumeric", str(len(comprobante.lineas)))

    if comprobante.orden_compra:
        orden = _el(raiz, NS_CAC, "OrderReference")
        _el(orden, NS_CBC, "ID", comprobante.orden_compra)

    proveedor = _el(raiz, NS_CAC, "AccountingSupplierParty")
    proveedor.append(_parte_emisor(comprobante))
    cliente = _el(raiz, NS_CAC, "AccountingCustomerParty")
    cliente.append(_parte_cliente(comprobante))

    _totales_impuestos(raiz, comprobante)

    legal = _el(raiz, NS_CAC, "LegalMonetaryTotal")
    _el(legal, NS_CBC, "LineExtensionAmount", _monto(comprobante.valor_venta), currencyID=moneda)
    _el(legal, NS_CBC, "TaxInclusiveAmount", _monto(comprobante.importe_total), currencyID=moneda)
    _el(legal, NS_CBC, "PayableAmount", _monto(comprobante.importe_total), currencyID=moneda)

    for posicion, linea in enumerate(comprobante.lineas, start=1):
        _linea_xml(raiz, linea, posicion, moneda)

    return raiz


def a_xml(comprobante: Comprobante, indentar: bool = True) -> bytes:
    """Serializa el comprobante como XML UTF-8."""
    raiz = construir(comprobante)
    if indentar:
        ET.indent(raiz, space="  ")
    return ET.tostring(raiz, encoding="utf-8", xml_declaration=True)


def guardar(comprobante: Comprobante, directorio: str = ".", indentar: bool = True) -> str:
    """Escribe el XML con el nombre que exige SUNAT y devuelve la ruta."""
    from pathlib import Path

    destino = Path(directorio) / f"{comprobante.nombre_archivo}.xml"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(a_xml(comprobante, indentar=indentar))
    return str(destino)
