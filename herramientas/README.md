# Actualización del dashboard de Facturación semanal

Pipeline probado el 25-nov-2026 contra el Excel del corte 20-nov: reprodujo
exactamente los 11 meses del dashboard hecho a mano.

```bash
mkdir -p /tmp/ventas && cp "Informe de Ventas.xlsx" /tmp/ventas/
python3 -I herramientas/generar_datos.py /tmp/ventas/Informe\ de\ Ventas.xlsx /tmp/salida
python3 -I herramientas/aplicar_datos.py "FACTURACION SEMANAL/index.html" /tmp/nuevo.html /tmp/salida
node herramientas/validar.js /tmp/nuevo.html     # debe terminar en "Todas las validaciones pasaron"
cp /tmp/nuevo.html "FACTURACION SEMANAL/index.html"
```

Después hay que actualizar a mano, en el `index.html` de la raíz:
el chip `Corte: <día> de <mes>`, la línea del `<footer class="note">` del dashboard,
y en `window.PORTAL.informes` el objeto `id: 'facturacion'` con
`actualizado` (momento de la publicación) y `periodo` (`'Corte al <día> de <mes>'`).

## Trampas del Excel, ya resueltas en el generador

- Algunas hojas traen una **columna vacía al inicio** (las de enero) y otras una
  **columna extra `Sucursal`** (Octubre Incomelec). Por eso las columnas se mapean
  **por nombre de cabecera**, nunca por posición. Si se rompe algo, mirar primero aquí.
- Los nombres de hoja son inconsistentes: `Febrero Incomlec`, `Marzo Suplec ` (con
  espacio final), `Mayo Incomelec `. El mes en curso va en `Incomelc` / `Suplec`, sin mes.
- `monthlyData` y `weeklyData` salen de la hoja `ACUMULADO`; los clientes y las
  facturas, de las hojas por mes. No se mezclan.
- Las semanas finales en cero se recortan (el mes en curso trae semanas futuras vacías).
- `clientData` lleva además la clave `Acumulado` con la suma de todos los meses.

## Criterio pendiente de confirmar con el cliente

En la hoja `ACUMULADO`, la fila *Total Facturado* **no** suma Intercompany de enero a
junio, pero **sí** de julio en adelante. La columna *Total 2026* sí lo suma siempre.
El dashboard sigue el criterio de *Total 2026* (Suplec + Incomelec + Intercompany en
todos los meses), que da un total anual de $30.269.270.998. Si se adoptara el criterio
de *Total Facturado*, el año bajaría $922.681.132. No cambiar esto sin que el cliente
lo decida.
