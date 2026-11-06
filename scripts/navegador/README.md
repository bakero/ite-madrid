# Extracción desde el navegador

Las fuentes municipales no permiten descargar los datos desde un servidor:

- madrid.es devuelve listados HTML paginados;
- el Registro ITE es un formulario POST en ISO-8859-1 que solo responde a peticiones del mismo origen;
- los servicios del Geoportal requieren CORS.

Por eso cada script se ejecuta **en la consola del navegador (F12 → Consola)**, con la página indicada abierta. Cada script descarga un archivo a la carpeta de Descargas.

| Script | Página que hay que tener abierta | Genera | Destino |
|---|---|---|---|
| `01_listados_madrid_es.js` | https://www.madrid.es/portales/munimadrid/es/Inicio/El-Ayuntamiento/Distritos/ | `madrid_listados_21distritos.json` | `datos/` (fuente del Excel de centros) |
| `02_consulta_ite_registro.js` | https://servpub.madrid.es/GITEP_WBFICHA/SGiteCons | `ite_resultados_AAAAMMDD_HHMM.json` | `scripts/sync.sh` o `ingest_export.py` |
| `03_calles_geoportal.js` | https://sigma.madrid.es/hosted/rest/services/CALLEJERO/CALLEJERO_ROTULACION_GEOMETRIAS/MapServer?f=json | `calles_madrid_con_nombres.json` (es JavaScript: renombrar a `calles.js`) | `app/calles.js` |
| `04_distritos_kml.js` | https://geoportal.madrid.es/ | `distritos_madrid_simpl.json` | `datos/` |

Notas sobre cada script:

- **02 (Registro ITE):** pide elegir `datos/pendientes_ite.json`. El servidor puede tardar mucho (la primera pasada completa llevó varias horas). El progreso se guarda en `localStorage`, así que si se recarga la página y se vuelve a pegar el script, continúa donde lo dejó. Con `ITE.descargar()` se descarga un volcado parcial en cualquier momento.
- **03 (calles):** descarga el trazado (capa 1:1.000) con el nombre oficial de cada vía; la jerarquía sale de las capas 1:20.000 y 1:25.000.
- **Descargas en `.tmp`:** algunos navegadores dejan la descarga como `.tmp` hasta que se confirma. `sync.sh` también busca esos archivos.

## Conjuntos de datos abiertos (descarga directa a `datos/`)

| Conjunto | Archivo usado |
|---|---|
| [202311 Colegios públicos](https://datos.madrid.es/dataset/202311-0-colegios-publicos) | `202311-0-colegios-publicos-json.json` |
| [300614 Centros educativos](https://datos.madrid.es/dataset/300614-0-centros-educativos) | `300614-5-centros-educativos-json.json` |
| [212790 Centros de educación](https://datos.madrid.es/dataset/212790-0-centros-educacion) | `212790-4-centros-educacion-json.json` |
| [202318 Escuelas infantiles](https://datos.madrid.es/dataset/202318-0-escuelas-infantiles) | `202318-2-escuelas-infantiles-json.json` |
| [300307 Empresas gestoras de EI](https://datos.madrid.es/dataset/300307-0-escuelas-infantiles-empresas) | `300307-1-escuelas-infantiles-empresas-csv.csv` |
| [207037 Escuelas Oficiales de Idiomas](https://datos.madrid.es/dataset/207037-0-idiomas-oficial) | `207037-0-idiomas-oficial-json.json` |
| [212904 Centros de enseñanza](https://datos.madrid.es/dataset/212904-0-centros-ensenanza) | `212904-2-centros-ensenanza-json.json` |
| [300497 Distritos municipales](https://datos.madrid.es/dataset/300497-0-distritos-municipales-madrid) | ver `04_distritos_kml.js` |
