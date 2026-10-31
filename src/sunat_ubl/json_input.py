"""Carga de comprobantes desde JSON (el formato que usa la CLI)."""

from __future__ import annotations

import json
from datetime import date, time
from pathlib import Path

from .models import Cliente, Comprobante, Emisor, Linea


def _fecha(valor: str) -> date:
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ValueError(f"Fecha inválida: {valor!r} (usa YYYY-MM-DD)") from None


def _hora(valor: str | None) -> time | None:
    if not valor:
        return None
    try:
        return time.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ValueError(f"Hora inválida: {valor!r} (usa HH:MM:SS)") from None


def _linea(datos: dict) -> Linea:
    if "precio_con_igv" in datos:
        return Linea.desde_precio_con_igv(
            descripcion=datos["descripcion"],
            cantidad=datos["cantidad"],
            precio_con_igv=datos["precio_con_igv"],
            tipo_afectacion=datos.get("tipo_afectacion", "10"),
            unidad=datos.get("unidad", "NIU"),
            codigo=datos.get("codigo"),
        )
    return Linea(
        descripcion=datos["descripcion"],
        cantidad=datos["cantidad"],
        valor_unitario=datos["valor_unitario"],
        tipo_afectacion=datos.get("tipo_afectacion", "10"),
        unidad=datos.get("unidad", "NIU"),
        codigo=datos.get("codigo"),
    )


def comprobante_desde_dict(datos: dict) -> Comprobante:
    try:
        emisor = datos["emisor"]
        cliente = datos["cliente"]
        return Comprobante(
            tipo=datos["tipo"],
            serie=datos["serie"],
            numero=datos["numero"],
            fecha=_fecha(datos["fecha"]),
            hora=_hora(datos.get("hora")),
            moneda=datos.get("moneda", "PEN"),
            observacion=datos.get("observacion"),
            orden_compra=datos.get("orden_compra"),
            emisor=Emisor(
                ruc=emisor["ruc"],
                razon_social=emisor["razon_social"],
                nombre_comercial=emisor.get("nombre_comercial"),
                direccion=emisor.get("direccion"),
                ubigeo=emisor.get("ubigeo"),
            ),
            cliente=Cliente(
                tipo_doc=cliente.get("tipo_doc", "6"),
                numero=cliente["numero"],
                razon_social=cliente["razon_social"],
                direccion=cliente.get("direccion"),
                email=cliente.get("email"),
            ),
            lineas=[_linea(linea) for linea in datos["lineas"]],
        )
    except KeyError as error:
        raise ValueError(f"Falta el campo obligatorio {error} en el JSON") from None


def comprobante_desde_archivo(ruta: str | Path) -> Comprobante:
    return comprobante_desde_dict(json.loads(Path(ruta).read_text(encoding="utf-8")))
