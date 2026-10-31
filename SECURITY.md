# Seguridad

## Reportar vulnerabilidades

Si encuentras un problema de seguridad en `sunat-ubl` (manejo de claves, validación de firma,
parsing de XML o CDR), **no abras un issue público**. Usa el reporte privado de vulnerabilidades
de GitHub: pestaña **Security → Report a vulnerability** en el repositorio. Incluye:

- Versión afectada
- Pasos para reproducir
- Impacto estimado

Responderemos en un máximo de 7 días y publicaremos el detalle solo después de liberar el fix.

## Aviso importante sobre el uso criptográfico

- La firma digital usa `signxml` sobre lxml. Los archivos de clave privada **nunca** deben
  commitearse ni incluirse en logs: este repositorio las lee únicamente desde rutas que tú
  indiques en tiempo de ejecución.
- La validación de la firma (`verificar_firma`) comprueba integridad y autenticidad del
  certificado, pero **no reemplaza** la validación oficial de SUNAT ni la del XSD.
- Antes de emitir comprobantes reales, prueba siempre en el entorno beta del contribuyente
  (SEE beta) con tu certificado de pruebas.
