import datetime
from pathlib import Path

import pytest

pytest.importorskip("signxml")
cryptography = pytest.importorskip("cryptography")

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from sunat_ubl import a_xml, comprobante_desde_archivo, firmar_xml, verificar_firma

EJEMPLO = Path(__file__).resolve().parent.parent / "examples" / "factura.json"


@pytest.fixture(scope="module")
def claves():
    clave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PRUEBAS SUNAT UBL")])
    ahora = datetime.datetime.now(datetime.timezone.utc)
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nombre)
        .issuer_name(nombre)
        .public_key(clave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - datetime.timedelta(days=1))
        .not_valid_after(ahora + datetime.timedelta(days=365))
        .sign(clave, hashes.SHA256())
    )
    return {
        "cert": certificado.public_bytes(serialization.Encoding.PEM),
        "key": clave.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    }


@pytest.fixture(scope="module")
def xml_sin_firmar():
    return a_xml(comprobante_desde_archivo(EJEMPLO), indentar=False)


@pytest.fixture(scope="module")
def xml_firmado(xml_sin_firmar, claves):
    return firmar_xml(xml_sin_firmar, claves["cert"], claves["key"])


def test_firma_valida(xml_firmado, claves):
    assert verificar_firma(xml_firmado, claves["cert"])


def test_firma_dentro_de_extension_content(xml_firmado):
    from lxml import etree

    raiz = etree.fromstring(xml_firmado)
    firma = raiz.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")
    assert firma is not None
    contenedor = raiz.find(
        ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent"
    )
    assert firma.getparent() is contenedor
    # la firma no debe quedar como hijo directo de Invoice
    assert etree.QName(raiz[-1]).localname == "InvoiceLine"


def test_firma_usa_sha256_y_c14n_exclusiva(xml_firmado):
    texto = xml_firmado.decode()
    assert "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256" in texto
    assert "http://www.w3.org/2001/10/xml-exc-c14n#" in texto
    assert "http://www.w3.org/2001/04/xmlenc#sha256" in texto


def test_documento_alterado_no_verifica(xml_firmado, claves):
    alterado = xml_firmado.replace(b"404.00", b"403.00", 1)
    assert alterado != xml_firmado
    assert not verificar_firma(alterado, claves["cert"])


def test_certificado_distinto_no_verifica(xml_firmado, claves):
    otra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "OTRO")])
    ahora = datetime.datetime.now(datetime.timezone.utc)
    otro = (
        x509.CertificateBuilder()
        .subject_name(nombre)
        .issuer_name(nombre)
        .public_key(otra.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - datetime.timedelta(days=1))
        .not_valid_after(ahora + datetime.timedelta(days=365))
        .sign(otra, hashes.SHA256())
    )
    assert not verificar_firma(xml_firmado, otro.public_bytes(serialization.Encoding.PEM))


def test_xml_sin_firma_no_verifica(xml_sin_firmar, claves):
    assert not verificar_firma(xml_sin_firmar, claves["cert"])


def test_xml_sin_extension_content(claves):
    with pytest.raises(ValueError, match="ExtensionContent"):
        firmar_xml(b"<Invoice/>", claves["cert"], claves["key"])


def test_acepta_rutas_de_archivo(xml_sin_firmar, claves, tmp_path):
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    cert_path.write_bytes(claves["cert"])
    key_path.write_bytes(claves["key"])
    firmado = firmar_xml(xml_sin_firmar, str(cert_path), str(key_path))
    assert verificar_firma(firmado, str(cert_path))


def test_cli_firma_un_xml(xml_sin_firmar, claves, tmp_path):
    from sunat_ubl.cli import main

    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    xml_path = tmp_path / "factura.xml"
    cert_path.write_bytes(claves["cert"])
    key_path.write_bytes(claves["key"])
    xml_path.write_bytes(xml_sin_firmar)

    codigo = main(["firmar", str(xml_path), "--cert", str(cert_path), "--clave", str(key_path)])
    assert codigo == 0
    salida = tmp_path / "factura-firmado.xml"
    assert salida.exists()
    assert verificar_firma(salida.read_bytes(), str(cert_path))


def test_cli_genera_y_firma_en_un_paso(claves, tmp_path):
    from sunat_ubl.cli import main

    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    cert_path.write_bytes(claves["cert"])
    key_path.write_bytes(claves["key"])

    codigo = main(
        [
            "generar",
            str(EJEMPLO),
            "-o",
            str(tmp_path),
            "--cert",
            str(cert_path),
            "--clave",
            str(key_path),
        ]
    )
    assert codigo == 0
    generado = tmp_path / "20999999990-01-F001-1.xml"
    assert generado.exists()
    assert verificar_firma(generado.read_bytes(), str(cert_path))


def test_cli_exige_cert_y_clave_juntos(tmp_path):
    from sunat_ubl.cli import main

    assert main(["generar", str(EJEMPLO), "-o", str(tmp_path), "--cert", "x.pem"]) == 1
