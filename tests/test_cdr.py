import io
import zipfile

import pytest

from sunat_ubl import leer_cdr

XML_ACEPTADO = """<?xml version="1.0" encoding="UTF-8"?>
<ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <cbc:UBLVersionID>2.0</cbc:UBLVersionID>
  <cbc:CustomizationID>1.0</cbc:CustomizationID>
  <cbc:ID>a1b2c3d4-0000-4000-8000-000000000001</cbc:ID>
  <cbc:IssueDate>2026-10-30</cbc:IssueDate>
  <cbc:IssueTime>15:42:11</cbc:IssueTime>
  <cac:SenderParty>
    <cac:PartyIdentification><cbc:ID>20131312955</cbc:ID></cac:PartyIdentification>
  </cac:SenderParty>
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:ReferenceID>F001-1</cbc:ReferenceID>
      <cbc:ResponseCode>0</cbc:ResponseCode>
      <cbc:Description>El comprobante fue registrado exitosamente</cbc:Description>
    </cac:Response>
  </cac:DocumentResponse>
  <cbc:Note>2335 - El comprobante fue aceptado</cbc:Note>
  <ds:Signature><ds:SignedInfo><ds:Reference><ds:DigestValue>abc123</ds:DigestValue></ds:Reference></ds:SignedInfo></ds:Signature>
</ApplicationResponse>
"""

XML_RECHAZADO = XML_ACEPTADO.replace(
    "<cbc:ResponseCode>0</cbc:ResponseCode>", "<cbc:ResponseCode>2800</cbc:ResponseCode>"
).replace(
    "El comprobante fue registrado exitosamente",
    "El comprobante fue rechazado: el RUC del emisor no está habido",
).replace("<cbc:Note>2335 - El comprobante fue aceptado</cbc:Note>", "")


def _zip(xml: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archivo:
        archivo.writestr("R-20999999990-01-F001-1.xml", xml)
    return buffer.getvalue()


def test_cdr_aceptado_desde_zip():
    cdr = leer_cdr(_zip(XML_ACEPTADO))
    assert cdr.aceptado
    assert not cdr.rechazado
    assert cdr.observado
    assert cdr.codigo == "0"
    assert cdr.referencia == "F001-1"
    assert cdr.identificador == "a1b2c3d4-0000-4000-8000-000000000001"
    assert cdr.fecha == "2026-10-30"
    assert cdr.hash == "abc123"
    assert cdr.notas == ("2335 - El comprobante fue aceptado",)


def test_cdr_aceptado_sin_observaciones():
    cdr = leer_cdr(XML_ACEPTADO.replace("<cbc:Note>2335 - El comprobante fue aceptado</cbc:Note>", "").encode())
    assert cdr.aceptado
    assert not cdr.observado


def test_cdr_rechazado():
    cdr = leer_cdr(_zip(XML_RECHAZADO))
    assert cdr.rechazado
    assert cdr.codigo == "2800"
    assert "no está habido" in cdr.descripcion


def test_xml_que_no_es_cdr():
    with pytest.raises(ValueError, match="no parece un CDR"):
        leer_cdr(b"<Invoice/>")


def test_zip_sin_xml():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archivo:
        archivo.writestr("leeme.txt", "nada")
    with pytest.raises(ValueError, match="ningún archivo XML"):
        leer_cdr(buffer.getvalue())
