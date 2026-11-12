# Trazabilidad de los datos de Ciudadano Madrid

Cada cifra de la web se puede seguir hasta el fichero oficial del que sale. Lo garantiza la base de datos
`ciudadano_madrid.sqlite` (se publica en GitHub Releases; no va en el repositorio por tamaño).

## Esquema

| Tabla | Qué guarda |
| --- | --- |
| `fuente` | Conjunto, servicio o página de origen: organismo, URL de su ficha pública, licencia, tipo de acceso (`api`, `descarga`, `extraccion`, `solicitud`), sección de la web, prioridad, frecuencia y años que cubre. |
| `descarga` | Cada fichero o página obtenida: URL exacta, fecha y hora (UTC), SHA-256, tamaño, formato, copia en Internet Archive o en GitHub Releases, script y commit que la procesaron, pasos para repetirla a mano, tabla y nº de filas cargadas. |
| `v_procedencia` | Vista que une las dos: lo que muestra el enlace «De dónde sale» de la web. |
| Tablas de datos | Cada fila lleva `_descarga_id`. Las tablas `ds_<conjunto>_<familia>` son los ficheros de datos.madrid.es cargados sin transformar (todas las columnas como texto) y además llevan `_recurso` (nombre del fichero en el portal) y `_periodo`. |

Ejemplo: ¿de dónde sale una licencia de obra?

```sql
SELECT l.direccion, l.ano, p.url, p.fecha, p.sha256, p.pasos
FROM ds_300375_relacion_de_licencias_de_obras l
JOIN v_procedencia p ON p.descarga_id = l._descarga_id
LIMIT 1;
```

## Cómo se repite una carga

```
python3 scripts/datos/migrar_existente.py     # datos del Mapa ITE con su procedencia
python3 scripts/datos/ckan_madrid.py           # conjuntos de scripts/datos/catalogo.py desde datos.madrid.es
python3 scripts/datos/ckan_madrid.py 300375    # un conjunto concreto
```

Los ficheros originales quedan en `crudos/<conjunto>/` con el mismo nombre que en el portal. Con
`CM_ARCHIVAR=1` se pide además una copia a Internet Archive (necesita acceso a web.archive.org).

## Reglas

- Los datos se cargan tal cual; las limpiezas y uniones se hacen en vistas o tablas derivadas que citan su origen.
- Los nombres de personas físicas no se publican en la web.
- El Registro de Edificios (ITE) no se republica: solo URL, fecha y pasos (requiere permiso de reutilización).
- Los datos cargados antes de este esquema (Mapa ITE, hasta el 11/11/2026) tienen `archivo_estado = 'pendiente: carga anterior al esquema'` y el SHA-256 del fichero que se guardó entonces en `datos/`.
