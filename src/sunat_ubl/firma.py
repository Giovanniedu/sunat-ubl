"""Firma digital XMLDSig de los XML de SUNAT.

Las dependencias criptográficas son opcionales: `pip install "sunat-ubl[firma]"`.
El núcleo del paquete sigue sin dependencias para generar y leer comprobantes.
"""

from __future__ import annotations

from pathlib import Path

from .models import Comprobante

NS_DS = "http://www.w3.org/2000/09/xmldsig#"
NS_EXT = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"

_MENSAJE_DEPENDENCIAS = (
    "La firma digital necesita dependencias opcionales. "
    'Instálalas con: pip install "sunat-ubl[firma]"'
)


def _dependencias():
    try:
        from lxml import etree
        from signxml import (
            CanonicalizationMethod,
            DigestAlgorithm,
            SignatureMethod,
            XMLSigner,
            XMLVerifier,
        )
    except ImportError as error:  # pragma: no cover - depende del entorno
        raise ImportError(_MENSAJE_DEPENDENCIAS) from error
    return etree, CanonicalizationMethod, DigestAlgorithm, SignatureMethod, XMLSigner, XMLVerifier


def _leer_pem(valor: str | Path | bytes, nombre: str) -> bytes:
    if isinstance(valor, bytes):
        return valor
    if isinstance(valor, Path):
        return valor.read_bytes()
    if "-----BEGIN" in valor:
        return valor.encode("utf-8")
    ruta = Path(valor)
    if not ruta.is_file():
        raise ValueError(f"No se encontró el archivo de {nombre}: {valor!r}")
    return ruta.read_bytes()


def firmar_xml(
    xml: bytes,
    certificado: str | Path | bytes,
    clave: str | Path | bytes,
    password: bytes | str | None = None,
) -> bytes:
    """Firma un XML ya generado y devuelve los bytes firmados.

    La firma se inserta dentro de `ext:UBLExtensions/ext:ExtensionContent`, que es
    donde la exige SUNAT. El documento no se reindenta después de firmar: cualquier
    cambio de espacios invalidaría el digest.
    """
    etree, CanonicalizationMethod, DigestAlgorithm, SignatureMethod, XMLSigner, _ = _dependencias()

    raiz = etree.fromstring(xml)
    contenedor = raiz.find(f".//{{{NS_EXT}}}ExtensionContent")
    if contenedor is None:
        raise ValueError("El XML no tiene ext:UBLExtensions/ext:ExtensionContent; regenera el comprobante")

    firmador = XMLSigner(
        signature_algorithm=SignatureMethod.RSA_SHA256,
        digest_algorithm=DigestAlgorithm.SHA256,
        c14n_algorithm=CanonicalizationMethod.EXCLUSIVE_XML_CANONICALIZATION_1_0,
    )
    firmado = firmador.sign(
        raiz,
        key=_leer_pem(clave, "clave privada"),
        cert=_leer_pem(certificado, "certificado"),
        passphrase=password.encode("utf-8") if isinstance(password, str) else password,
    )

    firma = firmado.find(f".//{{{NS_DS}}}Signature")
    if firma is None:
        raise RuntimeError("signxml no generó la firma")
    # signxml devuelve un árbol nuevo: el contenedor debe buscarse en él, no en el original.
    contenedor = firmado.find(f".//{{{NS_EXT}}}ExtensionContent")
    if contenedor is None:
        raise RuntimeError("el árbol firmado perdió ext:ExtensionContent")
    contenedor.append(firma)
    return etree.tostring(firmado, xml_declaration=True, encoding="utf-8")


def firmar(
    comprobante: Comprobante,
    certificado: str | Path | bytes,
    clave: str | Path | bytes,
    password: bytes | str | None = None,
) -> bytes:
    """Genera y firma el XML de un comprobante en un solo paso."""
    from .generator import a_xml

    return firmar_xml(a_xml(comprobante, indentar=False), certificado, clave, password)


def verificar_firma(xml: bytes, certificado: str | Path | bytes | None = None) -> bool:
    """Devuelve True si la firma es válida y el documento no fue alterado."""
    etree, _, _, _, _, XMLVerifier = _dependencias()
    try:
        XMLVerifier().verify(
            etree.fromstring(xml),
            x509_cert=_leer_pem(certificado, "certificado") if certificado else None,
            validate_schema=False,
        )
    except Exception:
        return False
    return True
