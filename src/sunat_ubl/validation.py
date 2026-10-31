"""Validaciones de identificadores peruanos (RUC, DNI, series)."""

from __future__ import annotations

_PESOS_RUC = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def validar_ruc(ruc: str) -> bool:
    """Valida un RUC de 11 dígitos con su dígito verificador (módulo 11)."""
    if not isinstance(ruc, str) or len(ruc) != 11 or not ruc.isdigit():
        return False
    if ruc[:2] not in {"10", "15", "16", "17", "20"}:
        return False
    suma = sum(int(d) * p for d, p in zip(ruc[:10], _PESOS_RUC))
    resto = 11 - (suma % 11)
    verificador = 0 if resto == 10 else 1 if resto == 11 else resto
    return verificador == int(ruc[10])


def validar_dni(dni: str) -> bool:
    return isinstance(dni, str) and len(dni) == 8 and dni.isdigit()


def validar_serie(serie: str, tipo_comprobante: str) -> bool:
    """La serie de factura empieza con F y la de boleta con B (4 caracteres)."""
    if not isinstance(serie, str) or len(serie) != 4:
        return False
    prefijo = {"01": "F", "03": "B"}.get(tipo_comprobante)
    if prefijo is None:
        return False
    return serie[0] == prefijo and all(c.isalnum() and c.upper() == c for c in serie[1:])
