# Changelog

## 0.1.0 — 2026-10-30

Primera versión publicable.

- XML UBL 2.1 de factura (01) y boleta (03) con los namespaces y el orden de elementos de SUNAT.
- Afectación del IGV: gravado (10), exonerado (20), inafecto (30) y exportación (40).
- Cuadratura del IGV derivada del precio con IGV, sin descuadre de un céntimo.
- Validación de RUC (módulo 11), DNI, series y montos.
- Lectura de CDR desde ZIP o XML, con código, descripción y observaciones.
- CLI `sunat-ubl` con los comandos `generar`, `cdr` y `ruc`.
- Cero dependencias en tiempo de ejecución.
