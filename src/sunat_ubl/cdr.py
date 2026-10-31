"""Lectura del CDR (Constancia de Recepción) que devuelve SUNAT."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class Cdr:
    codigo: str
    descripcion: str
    notas: tuple[str, ...] = ()
    referencia: str | None = None
    fecha: str | None = None
    hash: str | None = None
    identificador: str | None = None

    @property
    def aceptado(self) -> bool:
        return self.codigo == "0"

    @property
    def observado(self) -> bool:
        """Aceptado, pero con observaciones que conviene revisar."""
        return self.aceptado and bool(self.notas)

    @property
    def rechazado(self) -> bool:
        return not self.aceptado


def _local(etiqueta: str) -> str:
    return etiqueta.rsplit("}", 1)[-1]


def _texto(raiz: ET.Element, nombre: str) -> str | None:
    for elemento in raiz.iter():
        if _local(elemento.tag) == nombre and elemento.text:
            return elemento.text.strip()
    return None


def _hijo_directo(raiz: ET.Element, nombre: str) -> str | None:
    for elemento in list(raiz):
        if _local(elemento.tag) == nombre and elemento.text:
            return elemento.text.strip()
    return None


def _textos(raiz: ET.Element, nombre: str) -> tuple[str, ...]:
    return tuple(
        elemento.text.strip()
        for elemento in raiz.iter()
        if _local(elemento.tag) == nombre and elemento.text and elemento.text.strip()
    )


def _extraer_xml(datos: bytes) -> bytes:
    if datos[:2] != b"PK":
        return datos
    with zipfile.ZipFile(io.BytesIO(datos)) as archivo:
        xmls = [n for n in archivo.namelist() if n.lower().endswith(".xml")]
        if not xmls:
            raise ValueError("El ZIP no contiene ningún archivo XML")
        return archivo.read(xmls[0])


def leer_cdr(origen: bytes | str | Path) -> Cdr:
    """Parsea el CDR desde bytes, un ZIP o un XML suelto."""
    if isinstance(origen, (str, Path)):
        datos = Path(origen).read_bytes()
    else:
        datos = origen
    raiz = ET.fromstring(_extraer_xml(datos))
    codigo = _texto(raiz, "ResponseCode")
    if codigo is None:
        raise ValueError("El XML no parece un CDR: falta cbc:ResponseCode")
    return Cdr(
        codigo=codigo,
        descripcion=_texto(raiz, "Description") or "",
        notas=_textos(raiz, "Note"),
        referencia=_texto(raiz, "ReferenceID"),
        fecha=_hijo_directo(raiz, "IssueDate"),
        hash=_texto(raiz, "DigestValue"),
        identificador=_hijo_directo(raiz, "ID"),
    )
