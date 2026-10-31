# Contribuir

¡Gracias por el interés! Este proyecto apunta a que facturar electrónicamente en Perú sea
menos doloroso. Toda ayuda cuenta: código, reportes de bug, correcciones de documentación
o datos de catálogos de SUNAT que estén desactualizados.

## Entorno

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Convenciones

- Python 3.9+, sin dependencias en el núcleo (`src/sunat_ubl`).
- Los montos usan `decimal.Decimal` con redondeo comercial; nada de `float` para dinero.
- Los catálogos de SUNAT viven en `catalogs.py` y deben citar el número de catálogo oficial.
- Todo comportamiento nuevo lleva test en `tests/`.
- Los mensajes de error van en español, como el resto de la librería.

## Pull requests

1. Abre un issue primero si el cambio es grande, para no trabajar en algo que ya está en curso.
2. Una rama por cambio, PR contra `main`.
3. `python -m pytest` en verde antes de pedir review.
4. Describe qué problema resuelve el cambio y cómo lo probaste.

## Fuentes oficiales

Al tocar estructuras de XML, totales o catálogos, respalda el cambio con la documentación
oficial de SUNAT (RS 097-2012/SUNAT y sus anexos, o la guía del SEE vigente) y cítala en el PR.
