"""Catálogos oficiales de SUNAT usados en comprobantes electrónicos."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

TASA_IGV = Decimal("0.18")

TIPOS_COMPROBANTE = {
    "01": "Factura electrónica",
    "03": "Boleta de venta electrónica",
}

PREFIJO_SERIE = {
    "01": "F",
    "03": "B",
}

TIPOS_DOC_IDENTIDAD = {
    "0": "Doc. tributario no domiciliado sin RUC",
    "1": "DNI",
    "4": "Carné de extranjería",
    "6": "RUC",
    "7": "Pasaporte",
    "A": "Cédula diplomática",
}

# Catálogo 05: tributos
TRIBUTOS = {
    "1000": ("IGV", "VAT"),
    "9995": ("EXP", "FRE"),
    "9997": ("EXO", "VAT"),
    "9998": ("INAF", "FRE"),
}

# Catálogo 07: tipo de afectación del IGV
AFECTACIONES = {
    "10": ("Gravado - operación onerosa", "S", "1000"),
    "20": ("Exonerado - operación onerosa", "E", "9997"),
    "30": ("Inafecto - operación onerosa", "O", "9998"),
    "40": ("Exportación de bienes", "G", "9995"),
}

UNIDADES = {
    "NIU": "Unidad",
    "ZZ": "Servicio",
    "KGM": "Kilogramo",
    "LTR": "Litro",
    "MTR": "Metro",
    "BX": "Caja",
    "PK": "Paquete",
}


@dataclass(frozen=True)
class Afectacion:
    codigo: str
    descripcion: str
    categoria: str
    tributo: str
    tasa: Decimal

    @property
    def gravada(self) -> bool:
        return self.codigo == "10"

    @property
    def exenta(self) -> bool:
        return not self.gravada


def afectacion(codigo: str) -> Afectacion:
    try:
        descripcion, categoria, tributo = AFECTACIONES[codigo]
    except KeyError:
        raise ValueError(
            f"Tipo de afectación '{codigo}' no soportado. "
            f"Usa uno de: {', '.join(sorted(AFECTACIONES))}"
        ) from None
    return Afectacion(
        codigo=codigo,
        descripcion=descripcion,
        categoria=categoria,
        tributo=tributo,
        tasa=TASA_IGV if codigo == "10" else Decimal("0"),
    )
