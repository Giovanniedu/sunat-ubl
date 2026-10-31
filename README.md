# sunat-ubl

Genera el **XML UBL 2.1** de facturas y boletas electrónicas del Perú y lee el **CDR** de SUNAT.
Sin dependencias: solo la librería estándar de Python.

```python
from datetime import date
from sunat_ubl import Cliente, Comprobante, Emisor, Linea, guardar

factura = Comprobante(
    tipo="01", serie="F001", numero=1, fecha=date(2026, 10, 30),
    emisor=Emisor(ruc="20999999990", razon_social="SERVICIOS DEMO PERU SAC"),
    cliente=Cliente(tipo_doc="6", numero="20512345671", razon_social="CLIENTE SAC"),
    lineas=[
        Linea("Consultoría", cantidad=2, valor_unitario="100.00", unidad="ZZ"),
        Linea.desde_precio_con_igv("Soporte", cantidad=1, precio_con_igv=118),
        Linea("Servicio exonerado", cantidad=1, valor_unitario="50.00", tipo_afectacion="20"),
    ],
)
guardar(factura, "salida")  # salida/20999999990-01-F001-1.xml
```

## Por qué existe

Integrar con el SEE-SOL de SUNAT obliga a armar a mano un XML UBL 2.1 con namespaces,
catálogos de afectación del IGV y reglas de redondeo que, si se equivocan por un céntimo,
terminan en un rechazo con código y sin explicación útil. Esta librería resuelve esa capa:

- **Cuadratura exacta.** Si partes de un precio con IGV (100.00), la base queda en 84.75 y el
  IGV en 15.25, no en 15.26. Base + IGV siempre suma lo que paga el cliente.
- **Total por línea redondeado** a 2 decimales, que es como SUNAT valida los totales.
- **Catálogos oficiales**: afectación del IGV (10, 20, 30, 40), tributos (1000, 9995, 9997, 9998),
  tipos de documento de identidad y unidades de medida.
- **Nombre de archivo correcto**: `RUC-TIPO-SERIE-NUMERO.xml`.
- **Validación temprana** de RUC (módulo 11), DNI, series y montos, con mensajes en español.
- **CDR**: lee el ZIP o el XML que devuelve SUNAT y expone código, descripción y observaciones.

## Instalación

```bash
pip install sunat-ubl
```

Desde el repositorio, sin instalar nada:

```bash
python -m pytest          # 51 tests, sin dependencias
```

## CLI

```bash
sunat-ubl generar examples/factura.json -o salida   # imprime la ruta del XML
sunat-ubl cdr R-20999999990-01-F001-1.zip           # ACEPTADO / RECHAZADO + observaciones
sunat-ubl ruc 20100070970                           # válido por dígito verificador
```

Salida del `cdr`:

```
ACEPTADO CON OBSERVACIONES (0): El comprobante fue registrado exitosamente
comprobante: F001-1
observación: 2335 - El comprobante fue aceptado
```

## Formato JSON

`examples/factura.json` es un ejemplo completo. Las líneas aceptan `valor_unitario`
(sin IGV) o `precio_con_igv` (lo que paga el cliente):

```json
{
  "tipo": "01", "serie": "F001", "numero": 1,
  "fecha": "2026-10-30", "hora": "15:42:10", "moneda": "PEN",
  "emisor":  { "ruc": "20999999990", "razon_social": "SERVICIOS DEMO PERU SAC" },
  "cliente": { "tipo_doc": "6", "numero": "20512345671", "razon_social": "CLIENTE SAC" },
  "lineas": [
    { "descripcion": "Consultoría", "cantidad": 2, "valor_unitario": 100.0, "unidad": "ZZ" },
    { "descripcion": "Soporte", "cantidad": 1, "precio_con_igv": 118.0, "unidad": "ZZ" }
  ]
}
```

## Qué hace y qué no

| Sí | Todavía no |
| --- | --- |
| XML UBL 2.1 de factura (01) y boleta (03) | Notas de crédito (07) y débito (08) |
| IGV, exonerado, inafecto y exportación | ISC e ICBPER |
| Totales, catálogos y validaciones | Firma digital XMLDSig |
| Lectura de CDR | Envío al SEE-SOL (SUNAT solo acepta SOAP con certificado) |

El XML sale **sin firmar**: el nodo `ext:UBLExtensions` se incluye vacío a propósito para que
agregues tu firma con `xmlsec` o `signxml` y tu certificado digital antes de enviarlo.
Esta librería no reemplaza la validación oficial de SUNAT.

## API

```python
from sunat_ubl import a_xml, construir, guardar, leer_cdr, validar_ruc

xml_bytes = a_xml(factura)           # bytes UTF-8 con declaración
raiz = construir(factura)            # xml.etree.ElementTree.Element
cdr = leer_cdr("R-...-CDR.zip")
cdr.aceptado, cdr.codigo, cdr.notas, cdr.referencia
```

## Desarrollo

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Licencia

MIT. Ver [LICENSE](LICENSE).
