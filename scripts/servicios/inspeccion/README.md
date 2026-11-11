# Herramientas para revisar pliegos a mano

Todas leen los textos de `PLIEGOS_TXT` (salida de `descarga_pliegos.py`).

- `ver.py <fichero.txt> <desde> <hasta>`: muestra un tramo de líneas sin las líneas de firma.
- `regla.py <fichero.txt> <desde> <hasta> [ancho]`: tramo con regla de columnas para ver la posición de cada columna.
- `pos.py <fichero.txt> <línea>:<texto> ...`: posición (centro) de un texto en una línea; sirve para fijar `col` y `name_end` en `datos/servicios/reparto_pliegos_cfg.json`.

Flujo: localizar la tabla de m² u horas del pliego, fijar en la configuración el modo (`linea`, `bloque`, `totales` o `ancla`), el documento, el rango, el lote y la columna; ejecutar `reparto_pliegos.py`; revisar las asignaciones aproximadas (`how` = fz, pos, addr, prev) y anular las malas con `anular`.
