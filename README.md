# Incomlec · Portal de Informes de Contabilidad

Sitio estático publicado en Cloudflare Pages.

## Estructura

| Ruta | Informe | Frecuencia |
|---|---|---|
| `/` | Portal de informes | — |
| `/CARTERA/` | Cartera | Semanal (viernes) |
| `/FACTURACION SEMANAL/` | Facturación semanal | Semanal (viernes) |
| `/INFORME EEFF/` | Estados financieros | Mensual (día 25) |
| `/TAREAS/` | Tareas | Mensual (día 7) |
| `/PLAN ESTRATEGICO/` | Plan estratégico | Mensual (día 7) |
| `/REQUERIMIENTOS GESTION INTEGRAL/` | Requerimientos | Por demanda |

Cada informe es un `index.html` autocontenido (sin dependencias de build).

## Cómo actualizar un informe

1. Reemplazar el `index.html` de la carpeta correspondiente.
2. Actualizar el campo `actualizado` de ese informe en `window.PORTAL.informes` dentro del `index.html` de la raíz.
3. Commit a `main`: Cloudflare Pages publica automáticamente.

Alternativa: el dashboard puede publicar su propia fecha en su `<head>` y el portal la lee sola:

```html
<meta name="lidato:actualizado" content="2026-11-20T13:00-05:00">
<meta name="lidato:periodo" content="Semana 47 · 2026">
```
