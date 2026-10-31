"""sunat-ubl: facturas y boletas electrónicas del Perú sin dependencias."""

from __future__ import annotations

from .catalogs import TASA_IGV, TIPOS_COMPROBANTE, TIPOS_DOC_IDENTIDAD, afectacion
from .cdr import Cdr, leer_cdr
from .generator import a_xml, construir, guardar
from .json_input import comprobante_desde_archivo, comprobante_desde_dict
from .models import Cliente, Comprobante, Emisor, Linea, dinero
from .validation import validar_dni, validar_ruc, validar_serie

__version__ = "0.1.0"

__all__ = [
    "TASA_IGV",
    "TIPOS_COMPROBANTE",
    "TIPOS_DOC_IDENTIDAD",
    "Cdr",
    "Cliente",
    "Comprobante",
    "Emisor",
    "Linea",
    "a_xml",
    "afectacion",
    "comprobante_desde_archivo",
    "comprobante_desde_dict",
    "construir",
    "dinero",
    "guardar",
    "leer_cdr",
    "validar_dni",
    "validar_ruc",
    "validar_serie",
    "__version__",
]
