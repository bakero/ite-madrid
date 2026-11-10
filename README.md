# Mapa ITE de edificios públicos de Madrid

Este proyecto sitúa en un mapa del municipio de Madrid los centros e instalaciones públicas de los 21 distritos. Cada edificio se colorea según el estado de su **última Inspección Técnica de Edificios (ITE/IEE)** en el Registro municipal. Los edificios sin ITE aparecen en gris.

La aplicación web es estática y está en `app/`. Tiene cinco páginas:

| Página | Qué hace |
|---|---|
| 🗺️ Mapa | Mapa con filtros (estado, distrito, tipo, subtipo, plazo de ITE, búsqueda) y «Cerca de…» (tu ubicación o una dirección, con radio). Al hacer clic en un edificio se abre su ficha, que se puede compartir con un enlace directo (`#edificio=lat,lng`) y desde la que se puede avisar de un error. |
| ⚠️ Lo más urgente | Desfavorables sin subsanar (de la más antigua a la más reciente), plazos de ITE/IEE vencidos y los que vencen este año y los dos siguientes. |
| 📊 Panel | Panel de tipo Power BI con segmentadores, KPIs, gráficos con filtrado cruzado y una tabla. |
| 📄 Informe PDF | Informe descargable de un distrito o de todo Madrid. |
| ❓ Ayuda y datos | Fuentes, tratamiento de los datos, limitaciones y fecha de la última descarga. |

**Datos:** 6.338 centros en 5.211 edificios, con 4.966 direcciones consultadas en el Registro. La última descarga es del 03/11/2026.

| Estado (por dirección) | Nº | Color |
|---|---|---|
| Favorable | 1.703 | verde |
| Desfavorable pendiente de subsanar | 626 | rojo |
| Desfavorable subsanada | 296 | naranja |
| IEE complementario | 78 | morado |
| Sin ITE | 882 | gris |
| No consultable / error del Registro | 1.381 | gris hueco |

## Publicar en GitHub Pages

El flujo de trabajo `.github/workflows/pages.yml` publica la carpeta `app/` cada vez que se hace push a `main` con cambios en ella.

Para activarlo la primera vez, ve a **Settings → Pages → Build and deployment → Source: GitHub Actions**. La web quedará en `https://bakero.github.io/ite-madrid/`.

Para usar la app en local, basta con abrir `app/index.html` en el navegador. Necesita conexión para cargar las librerías desde CDN: Chart.js 4.4.1, jsPDF 2.5.1, jspdf-autotable 3.8.2 (cdnjs) y la fuente Inter (Google Fonts). Los iconos ([Lucide](https://lucide.dev), licencia ISC) van integrados como SVG. El mapa se dibuja en canvas con datos propios, sin teselas externas.

## Estructura

```
app/                       Web estática (lo que se publica)
  index.html               Aplicación completa (HTML + CSS + JS)
  data.js                  Centros + ITE + contornos de distrito (generado por ingest_export.py)
  calles.js                Ejes de viario del callejero oficial (generado por 03_calles_geoportal.js)
  inversiones.js           Historial de inversión por edificio (Puente de Vallecas)
  servicios.js             Servicios contratados por edificio (Puente de Vallecas)
  empresas.js              Empresas de servicios por distrito (todo Madrid)
ite_madrid.sqlite          Base de datos con toda la información
centros_ite_madrid.xlsx    Exportación a Excel (Centros + ITE, Resumen por distrito, Fuentes)
datos/                     Datos de origen descargados y volcados intermedios
scripts/
  build_db.py              Crea la BD desde datos/ y genera datos/pendientes_ite.json
  ingest_export.py         Carga un volcado ITE en la BD y regenera el Excel y app/data.js
  reclasificacion.py       Reglas de corrección de tipo/subtipo de edificio
  coordenadas_manual.py    Coordenadas geocodificadas a mano (CartoCiudad) para centros sin ellas
  vulnerabilidad.py        Barrios (contornos) e IGUALA: asigna barrio a cada centro, renta por barrio, IVTA por distrito
  sync.sh                  Busca el volcado ITE más completo en Descargas y lo carga
  navegador/               Extracción web: scripts para pegar en la consola del navegador
```

## Base de datos (`ite_madrid.sqlite`)

| Tabla | Contenido |
|---|---|
| `fuentes` | Cada fuente con URL, archivo y nº de registros |
| `distritos` | Los 21 distritos con su contorno simplificado |
| `direcciones` | Direcciones únicas (4.966) con coordenadas |
| `centros` | Centros (6.388) con tipo/subtipo, tipo original, categoría de datos.madrid.es, fuente y `excluido` (50 sin dirección ni coordenadas, que no son edificios) |
| `ite` | Resultado de la consulta al Registro por dirección: estado calculado, dictamen, expediente, órdenes de ejecución, fechas, `origen` |
| `coordenadas_manual` | 8 coordenadas obtenidas con CartoCiudad |
| `barrios` | 131 barrios con su contorno simplificado; `centros.cod_barrio` indica el barrio de cada centro por coordenadas |
| `barrios_indicadores` | Renta neta media por hogar y otros descriptivos por barrio y año (IGUALA, 2020–2024) |
| `distritos_vulnerabilidad` | IVTA y sus 5 esferas por distrito y año (IGUALA, 2020–2024) |
| vista `v_centros_ite` | `centros` LEFT JOIN `ite` |

Ejemplo:

```sql
SELECT distrito, estado_inspeccion, COUNT(*) FROM v_centros_ite
WHERE COALESCE(excluido,'')='' GROUP BY 1,2;
```

> Si la carpeta está en una unidad sincronizada o montada y SQLite da `disk I/O error`, trabaja sobre una copia local: `ITE_DB=/tmp/ite_madrid.sqlite`. `sync.sh` ya lo hace así.

## Cómo actualizar los datos

Las webs del Ayuntamiento solo se pueden consultar desde un navegador (formularios y CORS), así que la extracción se hace con scripts que se pegan en la consola. Ver [`scripts/navegador/README.md`](scripts/navegador/README.md).

1. **Listados de centros** (opcional, si cambian): ejecuta `01_listados_madrid_es.js` en www.madrid.es. Obtienes `madrid_listados_21distritos.json`, que pasa a `datos/centros_madrid_21_distritos_ITE.xlsx`.
2. **Datos abiertos:** descarga los ficheros de datos.madrid.es en `datos/` (los enlaces están en el README de `navegador/`).
3. **Construir la BD:** `python3 scripts/build_db.py`. Genera `datos/pendientes_ite.json`.
4. **Consultar la ITE:** ejecuta `02_consulta_ite_registro.js` en servpub.madrid.es y elige `pendientes_ite.json`. Obtienes `ite_resultados_AAAAMMDD_HHMM.json`.
5. **Cargar y regenerar:** `python3 scripts/ingest_export.py datos/ite_resultados_….json` (o `scripts/sync.sh`). Actualiza la BD, `centros_ite_madrid.xlsx` y `app/data.js`.
6. **Calles y distritos** (rara vez): ejecuta `03_calles_geoportal.js` y `04_distritos_kml.js`.
7. **Barrios y vulnerabilidad** (una vez al año): descarga de datos.madrid.es el SHP de barrios ([Límites administrativos actuales](https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas)) y el fichero «Datos globales y por esferas para distritos» de [IGUALA](https://datos.madrid.es/dataset/300577-0-iguala-vulnerabilidad) en `datos/vulnerabilidad/`. Después ejecuta `python3 scripts/vulnerabilidad.py datos/vulnerabilidad/barrios_shp.zip datos/vulnerabilidad/iguala_ivta_global.xlsx` y luego `ingest_export.py`. Requiere `pyshp` y `pyproj`.

`ingest_export.py` aplica, en este orden:

1. completa coordenadas (desde `direcciones` y `coordenadas_manual`);
2. excluye lo que no es edificio;
3. asigna distrito por punto-en-polígono cuando falta;
4. unifica Educación/Educativo;
5. aplica `reclasificacion.py`.

Requisitos: Python 3.9+ con `openpyxl`.

## Cómo se calcula el estado de la ITE

Para cada dirección se toma la ITE/IEE con la fecha de presentación más reciente:

- **Favorable**: dictamen favorable.
- **Desfavorable pendiente**: dictamen desfavorable sin subsanar. **Desfavorable subsanada**: la orden de ejecución asociada indica deficiencias subsanadas.
- **IEE complementario**: el último expediente es un IEE complementario.
- **Sin ITE**: la ficha existe pero no tiene inspecciones.
- **No consultable**: sin número de portal, vial no encontrado o ambiguo, o error del propio Registro («ERROR con BDC»).

Un edificio (centros agrupados por coordenadas redondeadas a 5 decimales) toma el estado más grave de sus centros.

Los datos del Registro **no tienen carácter de certificado**. Conviene comprobar la «Denominación en el Registro» para confirmar que la ficha corresponde al edificio del centro.

## Avisos de errores (corrección ciudadana)

El botón «¿Ubicación o datos incorrectos?» de cada ficha abre un issue con la plantilla `.github/ISSUE_TEMPLATE/correccion.yml` y los datos del edificio ya rellenados. Se revisa a mano. Las direcciones corregidas se añaden a la base de datos (como las coordenadas de `coordenadas_manual.py`) y se vuelve a consultar la ITE.

## Fuentes y licencias

Datos del **Ayuntamiento de Madrid**, reutilizados según sus condiciones de uso (atribución, equivalente a CC BY 4.0):

- [madrid.es](https://www.madrid.es): «Direcciones y teléfonos» y «Recursos educativos públicos» de los 21 distritos.
- [Registro de Edificios y Construcciones (ITE)](https://servpub.madrid.es/GITEP_WBFICHA/SGiteCons).
- [datos.madrid.es](https://datos.madrid.es): conjuntos 202311, 300614, 212790, 202318, 300307, 207037, 212904 y 300497 (distritos).
- [Geoportal](https://geoportal.madrid.es): callejero oficial (viario) y límites de distrito.
- [datos.madrid.es](https://datos.madrid.es): barrios municipales (900012) e IGUALA (300577): renta neta media por hogar por barrio e Índice de Vulnerabilidad Territorial Agregado por distrito.
- [CartoCiudad](https://www.cartociudad.es) (IGN): geocodificación de 8 direcciones y buscador de direcciones de «Cerca de…».

Iconos: [Lucide](https://lucide.dev) (ISC).

## Historial de inversión (prueba piloto: Puente de Vallecas)

La ficha de cada edificio de Puente de Vallecas muestra lo que consta de inversión en él, a partir de tres fuentes:

| Fuente | Periodo | Importe |
|---|---|---|
| Ejecución presupuestaria, fichero «Inversiones» (datos.madrid.es 211496) | 2014–2025 | pagado (obligaciones reconocidas) |
| Actividad contractual y contratos menores (datos.madrid.es 216876 y 300253) | 2015–2026 | adjudicado |
| Anuncios de contratación del BOE (Sección V-A) | 1995–2014 | adjudicado o, si falta, licitación |

Scripts en `scripts/inversiones/` y datos de entrada en `datos/inversiones/`:

1. `normaliza.py`: unifica los ficheros de contratos (`contratos_vallecas_filtrados.json` → `contratos_norm.json`).
2. `boe_parse.py`: extrae objeto, expediente e importe de los anuncios del BOE (`boe_vallecas_1995_2014.json` → `boe_match.json`).
3. `historial.py`: asigna cada registro a un edificio (`edificios.py`: por nombre, con el tipo de centro delante si el nombre es también el de una calle o barrio, o por dirección exacta) y genera `datos/inversiones/historial_pv.json` y `app/inversiones.js`.

Los registros que afectan a varios edificios se descartan. Las tres fuentes se solapan y no se suman. Antes de 2014 solo hay contratos grandes del BOE.

## Servicios contratados (prueba piloto: Puente de Vallecas)

Empresas e importes de limpieza, seguridad, auxiliares de información y mantenimiento de los edificios del distrito.

1. `scripts/servicios/normaliza_todo.py <carpeta_csv> todos.json`: lee todos los CSV de actividad contractual (216876) y contratos menores (300253).
2. `scripts/servicios/servicios.py todos.json servicios_pv.json`: selecciona los contratos de servicios de edificios que afectan a Puente de Vallecas.
3. `scripts/servicios/reparto.py <carpeta_pliegos>`: lee los pliegos y estudios económicos (texto de `pdftotext -layout`) y obtiene el peso de cada edificio (horas, coste o m²) → `reparto.json`.
4. `scripts/servicios/servicios_app.py servicios_pv.json reparto.json [enlaces.json]` → `app/servicios.js`.

El importe de cada edificio es una estimación proporcional; el coste anual usa el contrato vigente de cada servicio, con sus prórrogas. Datos intermedios en `datos/servicios/`.

## Empresas de servicios por distrito (todo Madrid)

Qué empresa presta la limpieza, la seguridad, los auxiliares de información y el mantenimiento de los edificios de cada Junta de Distrito, con el coste anual y el enlace público a cada licitación.

1. `scripts/servicios/empresas_distritos.py todos.json empresas_distritos.json [enlaces.json]`: contratos de servicios de edificios de las 21 Juntas de Distrito, con prórrogas, fecha de fin, vigencia y coste anual. Si el objeto inscrito es solo el nombre del lote, la categoría sale del título de la licitación (`enlaces.json`).
2. `enlaces.json` (`{expediente: [[idEvl, texto de la fila]]}`) se obtiene buscando cada expediente en el buscador de licitaciones de la Plataforma de Contratación del Sector Público (`scripts/navegador/05_plataforma_enlaces.js`, para pegar en la consola del navegador en el formulario de búsqueda).
3. `scripts/servicios/empresas_app.py empresas_distritos.json enlaces.json` → `app/empresas.js`.

Enlace público: `https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=<idEvl>`.
