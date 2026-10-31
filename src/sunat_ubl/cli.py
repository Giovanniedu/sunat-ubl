"""Línea de comandos: generar XML, leer CDR y validar RUC."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .cdr import leer_cdr
from .generator import guardar
from .json_input import comprobante_desde_archivo
from .validation import validar_ruc


def _cmd_generar(args: argparse.Namespace) -> int:
    try:
        comprobante = comprobante_desde_archivo(args.archivo)
        ruta = guardar(comprobante, directorio=args.salida, indentar=not args.sin_indentar)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(ruta)
    return 0


def _cmd_cdr(args: argparse.Namespace) -> int:
    try:
        cdr = leer_cdr(args.archivo)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    estado = "ACEPTADO" if cdr.aceptado else "RECHAZADO"
    if cdr.observado:
        estado = "ACEPTADO CON OBSERVACIONES"
    print(f"{estado} ({cdr.codigo}): {cdr.descripcion}")
    if cdr.referencia:
        print(f"comprobante: {cdr.referencia}")
    for nota in cdr.notas:
        print(f"observación: {nota}")
    return 0 if cdr.aceptado else 1


def _cmd_ruc(args: argparse.Namespace) -> int:
    valido = validar_ruc(args.numero)
    print("válido" if valido else "inválido")
    return 0 if valido else 1


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sunat-ubl",
        description="Genera XML UBL 2.1 de facturas y boletas para SUNAT, y lee CDR.",
    )
    parser.add_argument("--version", action="version", version=f"sunat-ubl {__version__}")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    generar = subparsers.add_parser("generar", help="Genera el XML a partir de un JSON")
    generar.add_argument("archivo", help="Ruta del JSON con el comprobante")
    generar.add_argument("-o", "--salida", default=".", help="Carpeta de salida (default: .)")
    generar.add_argument("--sin-indentar", action="store_true", help="XML en una sola línea")
    generar.set_defaults(func=_cmd_generar)

    cdr = subparsers.add_parser("cdr", help="Lee un CDR (ZIP o XML) de SUNAT")
    cdr.add_argument("archivo", help="Ruta del CDR")
    cdr.set_defaults(func=_cmd_cdr)

    ruc = subparsers.add_parser("ruc", help="Valida un RUC por dígito verificador")
    ruc.add_argument("numero", help="RUC de 11 dígitos")
    ruc.set_defaults(func=_cmd_ruc)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
