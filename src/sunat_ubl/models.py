"""Modelo de dominio para armar un comprobante electrónico."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .catalogs import (
    PREFIJO_SERIE,
    TIPOS_COMPROBANTE,
    TIPOS_DOC_IDENTIDAD,
    afectacion,
)
from .validation import validar_dni, validar_ruc, validar_serie

CENTIMOS = Decimal("0.01")


def dinero(valor: Decimal | str | int) -> Decimal:
    """Redondea a 2 decimales con redondeo comercial (medio hacia arriba)."""
    try:
        return Decimal(valor).quantize(CENTIMOS, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Monto inválido: {valor!r}") from None


def _decimal(valor: Decimal | str | int, nombre: str) -> Decimal:
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{nombre} inválido: {valor!r}") from None


@dataclass(frozen=True)
class Emisor:
    ruc: str
    razon_social: str
    nombre_comercial: str | None = None
    direccion: str | None = None
    ubigeo: str | None = None

    def __post_init__(self) -> None:
        if not validar_ruc(self.ruc):
            raise ValueError(f"RUC del emisor inválido: {self.ruc!r}")
        if not self.razon_social.strip():
            raise ValueError("La razón social del emisor es obligatoria")


@dataclass(frozen=True)
class Cliente:
    tipo_doc: str
    numero: str
    razon_social: str
    direccion: str | None = None
    email: str | None = None

    def __post_init__(self) -> None:
        if self.tipo_doc not in TIPOS_DOC_IDENTIDAD:
            raise ValueError(
                f"Tipo de documento '{self.tipo_doc}' no soportado. "
                f"Usa uno de: {', '.join(sorted(TIPOS_DOC_IDENTIDAD))}"
            )
        if self.tipo_doc == "6" and not validar_ruc(self.numero):
            raise ValueError(f"RUC del cliente inválido: {self.numero!r}")
        if self.tipo_doc == "1" and not validar_dni(self.numero):
            raise ValueError(f"DNI del cliente inválido: {self.numero!r}")
        if self.tipo_doc in {"0", "4", "7", "A"} and not self.numero.strip():
            raise ValueError("El número de documento del cliente es obligatorio")
        if not self.razon_social.strip():
            raise ValueError("La razón social del cliente es obligatoria")


@dataclass(frozen=True)
class Linea:
    descripcion: str
    cantidad: Decimal | str | int
    valor_unitario: Decimal | str | int
    tipo_afectacion: str = "10"
    unidad: str = "NIU"
    codigo: str | None = None
    precio_con_igv_unitario: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.descripcion.strip():
            raise ValueError("La descripción de la línea es obligatoria")
        cantidad = _decimal(self.cantidad, "cantidad")
        if cantidad <= 0:
            raise ValueError(f"La cantidad debe ser mayor a 0, recibido {cantidad}")
        valor = _decimal(self.valor_unitario, "valor unitario")
        if valor < 0:
            raise ValueError(f"El valor unitario no puede ser negativo: {valor}")
        afectacion(self.tipo_afectacion)
        if not 2 <= len(self.unidad) <= 3 or not self.unidad.isalpha() or self.unidad.upper() != self.unidad:
            raise ValueError(f"Unidad de medida inválida: {self.unidad!r} (ej. NIU, ZZ, KGM)")

    @classmethod
    def desde_precio_con_igv(
        cls,
        descripcion: str,
        cantidad: Decimal | str | int,
        precio_con_igv: Decimal | str | int,
        tipo_afectacion: str = "10",
        unidad: str = "NIU",
        codigo: str | None = None,
    ) -> "Linea":
        """Crea la línea a partir del precio que ve el cliente (IGV incluido).

        El valor unitario se calcula con 10 decimales para que el total de la
        línea, ya redondeado, coincida con el precio cobrado.
        """
        precio = _decimal(precio_con_igv, "precio")
        tasa = afectacion(tipo_afectacion).tasa
        valor = (precio / (Decimal("1") + tasa)).quantize(
            Decimal("0.0000000001"), rounding=ROUND_HALF_UP
        )
        return cls(
            descripcion=descripcion,
            cantidad=cantidad,
            valor_unitario=valor,
            tipo_afectacion=tipo_afectacion,
            unidad=unidad,
            codigo=codigo,
            precio_con_igv_unitario=precio,
        )

    @property
    def afectacion(self):
        return afectacion(self.tipo_afectacion)

    @property
    def subtotal(self) -> Decimal:
        """Valor de venta sin IGV (LineExtensionAmount)."""
        return dinero(_decimal(self.cantidad, "cantidad") * _decimal(self.valor_unitario, "valor"))

    @property
    def igv(self) -> Decimal:
        afectacion_linea = self.afectacion
        if afectacion_linea.exenta:
            return dinero(0)
        if self.precio_con_igv_unitario is not None:
            # El IGV se deriva del precio cobrado para que base + IGV cuadre
            # exactamente con lo que paga el cliente (evita el descuadre de 1 céntimo).
            cobrado = dinero(_decimal(self.cantidad, "cantidad") * self.precio_con_igv_unitario)
            return cobrado - self.subtotal
        return dinero(self.subtotal * afectacion_linea.tasa)

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.igv

    @property
    def precio_con_igv(self) -> Decimal:
        return self.total / _decimal(self.cantidad, "cantidad")


@dataclass
class Comprobante:
    tipo: str
    serie: str
    numero: int
    fecha: date
    emisor: Emisor
    cliente: Cliente
    lineas: list[Linea] = field(default_factory=list)
    hora: time | None = None
    moneda: str = "PEN"
    observacion: str | None = None
    orden_compra: str | None = None

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_COMPROBANTE:
            raise ValueError(
                f"Tipo de comprobante '{self.tipo}' no soportado todavía. "
                f"Usa uno de: {', '.join(sorted(TIPOS_COMPROBANTE))}"
            )
        if not validar_serie(self.serie, self.tipo):
            raise ValueError(
                f"Serie inválida para el tipo {self.tipo}: {self.serie!r} "
                f"(debe empezar con {PREFIJO_SERIE[self.tipo]}, 4 caracteres)"
            )
        if not isinstance(self.numero, int) or not 1 <= self.numero <= 99_999_999:
            raise ValueError(f"Número de comprobante inválido: {self.numero!r}")
        if isinstance(self.fecha, str) or not isinstance(self.fecha, date):
            raise ValueError("La fecha debe ser un objeto datetime.date")
        if isinstance(self.hora, str):
            raise ValueError("La hora debe ser un objeto datetime.time")
        if len(self.moneda) != 3 or not self.moneda.isalpha() or self.moneda.upper() != self.moneda:
            raise ValueError(f"Moneda inválida: {self.moneda!r} (ISO 4217, ej. PEN, USD)")
        if not self.lineas:
            raise ValueError("El comprobante necesita al menos una línea")

    @property
    def identificador(self) -> str:
        return f"{self.serie}-{self.numero}"

    @property
    def nombre_archivo(self) -> str:
        """Nombre exigido por SUNAT para el XML: RUC-TIPO-SERIE-NUMERO.xml."""
        return f"{self.emisor.ruc}-{self.tipo}-{self.serie}-{self.numero}"

    @property
    def total_gravado(self) -> Decimal:
        return sum((l.subtotal for l in self.lineas if l.afectacion.gravada), dinero(0))

    @property
    def total_exonerado(self) -> Decimal:
        return sum((l.subtotal for l in self.lineas if l.tipo_afectacion == "20"), dinero(0))

    @property
    def total_inafecto(self) -> Decimal:
        return sum((l.subtotal for l in self.lineas if l.tipo_afectacion == "30"), dinero(0))

    @property
    def total_exportacion(self) -> Decimal:
        return sum((l.subtotal for l in self.lineas if l.tipo_afectacion == "40"), dinero(0))

    @property
    def valor_venta(self) -> Decimal:
        """Suma de los valores de venta sin IGV (LegalMonetaryTotal/LineExtensionAmount)."""
        return sum((l.subtotal for l in self.lineas), dinero(0))

    @property
    def total_igv(self) -> Decimal:
        return sum((l.igv for l in self.lineas), dinero(0))

    @property
    def importe_total(self) -> Decimal:
        """Monto a pagar con IGV incluido (PayableAmount)."""
        return self.valor_venta + self.total_igv

    def subtotales_impuestos(self) -> list[dict]:
        """Agrupa base imponible e impuesto por tributo, en orden ascendente."""
        grupos: dict[str, dict] = {}
        for linea in self.lineas:
            afectacion_linea = linea.afectacion
            grupo = grupos.setdefault(
                afectacion_linea.tributo,
                {
                    "tributo": afectacion_linea.tributo,
                    "base": dinero(0),
                    "importe": dinero(0),
                    "categoria": afectacion_linea.categoria,
                    "tasa": afectacion_linea.tasa,
                    "motivo": linea.tipo_afectacion,
                },
            )
            grupo["base"] += linea.subtotal
            grupo["importe"] += linea.igv
        return [grupos[codigo] for codigo in sorted(grupos)]
