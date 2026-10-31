# Changelog

## 0.2.0 — 2026-10-30

- Firma digital XMLDSig (`rsa-sha256`, digest `sha256`, `exc-c14n`) insertada en
  `ext:UBLExtensions/ext:ExtensionContent`, donde la exige SUNAT.
- API nueva: `firmar`, `firmar_xml`, `verificar_firma` (con detección de documentos alterados).
- CLI: comando `firmar` y `generar --cert/--clave/--password` para firmar al generar.
- Extra opcional `[firma]` (signxml + lxml); el núcleo sigue sin dependencias.
- Assets del proyecto: banner, diagrama de flujo y social preview (PNG + SVG fuente).
- Docs de comunidad: CONTRIBUTING, SECURITY, dependabot y workflow de publicación a PyPI.
- 62 tests.

## 0.1.0 — 2026-10-30

Primera versión publicable.

- XML UBL 2.1 de factura (01) y boleta (03) con los namespaces y el orden de elementos de SUNAT.
- Afectación del IGV: gravado (10), exonerado (20), inafecto (30) y exportación (40).
- Cuadratura del IGV derivada del precio con IGV, sin descuadre de un céntimo.
- Validación de RUC (módulo 11), DNI, series y montos.
- Lectura de CDR desde ZIP o XML, con código, descripción y observaciones.
- CLI `sunat-ubl` con los comandos `generar`, `cdr` y `ruc`.
- Cero dependencias en tiempo de ejecución.
