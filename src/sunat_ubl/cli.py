"""Línea de comandos: generar XML, leer CDR y validar RUC."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .cdr import leer_cdr
from .firma import firmar, firmar_xml
from .generator import guardar, ruta_de
from .json_input import comprobante_desde_archivo
from .validation import validar_ruc


def _cmd_generar(args: argparse.Namespace) -> int:
    try:
        comprobante = comprobante_desde_archivo(args.archivo)
        if args.cert or args.clave:
            if not (args.cert and args.clave):
                raise ValueError("--cert y --clave deben usarse juntos")
            contenido = firmar(comprobante, args.cert, args.clave, args.password)
            ruta = ruta_de(comprobante, args.salida)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(contenido)
            print(ruta)
        else:
            print(guardar(comprobante, directorio=args.salida, indentar=not args.sin_indentar))
    except (ValueError, OSError, ImportError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def _cmd_firmar(args: argparse.Namespace) -> int:
    try:
        original = Path(args.archivo)
        firmado = firmar_xml(original.read_bytes(), args.cert, args.clave, args.password)
        destino = Path(args.salida) if args.salida else original.with_name(f"{original.stem}-firmado.xml")
        destino.write_bytes(firmado)
        print(destino)
    except (ValueError, OSError, ImportError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
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
    generar.add_argument("--cert", help="Certificado público en PEM: firma el XML al generarlo")
    generar.add_argument("--clave", help="Clave privada en PEM")
    generar.add_argument("--password", help="Contraseña de la clave privada, si tiene")
    generar.set_defaults(func=_cmd_generar)

    firmar_cmd = subparsers.add_parser("firmar", help="Firma un XML ya generado (XMLDSig)")
    firmar_cmd.add_argument("archivo", help="Ruta del XML sin firmar")
    firmar_cmd.add_argument("--cert", required=True, help="Certificado público en PEM")
    firmar_cmd.add_argument("--clave", required=True, help="Clave privada en PEM")
    firmar_cmd.add_argument("--password", help="Contraseña de la clave privada, si tiene")
    firmar_cmd.add_argument("-o", "--salida", help="Archivo de salida (default: <nombre>-firmado.xml)")
    firmar_cmd.set_defaults(func=_cmd_firmar)

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
