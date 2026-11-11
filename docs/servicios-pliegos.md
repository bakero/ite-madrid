# Reparto por edificio de los servicios de las Juntas (fuera de Puente de Vallecas)

Estado a 11/11/2026: 66 contratos vigentes. 24 con reparto leído del pliego, 40 pendientes de revisar (seguridad, servicios auxiliares y 7 de limpieza o mantenimiento), 1 escaneado (sin texto, necesita OCR) y 1 contrato de emergencia sin pliego. La tabla se genera con `python3 scripts/servicios/estado_pliegos.py`.

## Método

`scripts/servicios/reparto_pliegos.py` lee la tabla del pliego (o de su estudio económico) que da el peso de cada edificio y reparte el importe de cada lote en proporción:

- **Peso**: m² construidos en mantenimiento (y en limpieza si el pliego no da horas); horas de limpieza (al año, a la semana o al día, siempre la misma unidad dentro de un lote); horas o puestos en seguridad y servicios auxiliares.
- **Filas no asignadas**: las que no son un edificio del mapa (personal común a todos los centros, bolsas de horas, instalaciones elementales agrupadas, espacios que no están en el mapa, filas compartidas por dos edificios distintos) cuentan en el total del lote y no se asignan a nadie, para no inflar las cuotas. Si no se han podido leer todas las filas, `total_lote` añade sin asignar la diferencia con el total del pliego.
- **Revisión a mano**: todas las asignaciones aproximadas se revisan. Las tablas irregulares se transcriben a mano (modo `manual`) con la línea del texto del pliego, y las asignaciones dudosas se corrigen con la dirección que da el propio pliego (`fijar`) o se anulan (`anular`). Si una fila no se puede atribuir a un edificio con seguridad, queda sin asignar.
- Cada contrato indica en la web qué % de su importe se asigna a edificios del mapa (última columna).

Modos de `datos/servicios/reparto_pliegos_cfg.json`: `linea` (una fila por edificio; con `tablas` por rango de líneas y lote), `bloque`, `totales`, `ancla`, `manual` (filas transcritas: `[lote, peso, edificio|null, texto, línea]`), `sin` (sin reparto, con `motivo`). Opciones: `anular`, `fijar`, `filas` (filas manuales que completan una lectura automática), `total_lote`, `cats` (categoría corregida) y `nota`. El script rechaza claves de edificio que no existan en el mapa. Con expedientes como argumentos solo recalcula esos.

## Incidencias encontradas

- **Tetuán 300/2018/00448** figuraba como mantenimiento vigente hasta 2027. Es el lote 2 (limpieza) del contrato integral de 2018 y lo sustituyó 300/2022/00589 (limpieza desde 07/2023). Su fecha de fin salía de sumar como consecutivas las prórrogas de los tres lotes. Ahora las prórrogas con la misma duración formalizadas con menos de un mes de diferencia cuentan como una sola (`meses_prorroga` en `scripts/servicios/comun.py`, usada por `empresas_distritos.py` y `servicios_app.py`), y en esos casos la ficha no muestra el importe de la prórroga porque no se sabe cuál es el del lote. Aplicada a `empresas_distritos.json`, cambian cuatro fechas de fin: este contrato (deja de estar vigente) y tres de Hortaleza ya terminados (300/2018/01470, 300/2019/00002 y 300/2018/01475, con dos lotes prorrogados a la vez cada año).
- **San Blas-Canillejas 300/2025/01453, lote 2** (instalaciones deportivas): el CDM San Blas y el pabellón de Las Rosas, que son casi toda la superficie, no están en el mapa; el lote queda sin reparto.
- La Junta de Retiro incluye el Centro Clara Campoamor: el pliego da la misma dirección (Plaza Daoíz y Velarde, 2).
- Pendiente fuera de este trabajo: algunos edificios del mapa se llaman por el primer centro de su lista y no por el principal (p. ej. el CEIP Ciudad de Jaén aparece como «Centro de Día Infantil… (en CEIP Ciudad de Jaén)»).
- Filas que agrupan varios edificios distintos (p. ej. «Casa del Reloj» en Arganzuela, «CM Canillejas + CD Esfinge» en San Blas) no se asignan.

## Pendiente

Seguridad y servicios auxiliares (horas o puestos en tablas de formato muy variable); limpieza de Hortaleza (300/2024/00672) y Salamanca (300/2024/00154); mantenimiento de Moncloa-Aravaca (300/2024/00204), Barajas (300/2025/00468), Centro (300/2024/00883) y Salamanca (300/2022/00730); limpieza de Barajas (300/2025/02814); OCR del pliego escaneado de Barajas (300/2024/01423).

| Expediente | Distrito | Servicios | Miles €/año | Estado | % del importe asignado a edificios del mapa |
|---|---|---|---:|---|---:|
| 300/2022/00401 | Arganzuela | auxiliares | 588 | pendiente de revisar | — |
| 300/2024/00418 | Arganzuela | limpieza. mantenimiento | 3.138 | reparto leído del pliego | 82 % |
| 300/2023/00396 | Arganzuela | seguridad | 1.260 | pendiente de revisar | — |
| 300/2024/01423 | Barajas | limpieza | 370 | escaneado (sin texto) | — |
| 300/2025/02814 | Barajas | limpieza | 656 | pendiente de revisar | — |
| 300/2025/00468 | Barajas | mantenimiento | 635 | pendiente de revisar | — |
| 300/2023/00196 | Carabanchel | auxiliares | 1.181 | pendiente de revisar | — |
| 300/2024/00101 | Carabanchel | limpieza | 5.105 | reparto leído del pliego | 95 % |
| 300/2024/00679 | Carabanchel | mantenimiento | 1.257 | reparto leído del pliego | 94 % |
| 300/2024/01321 | Carabanchel | seguridad | 822 | pendiente de revisar | — |
| 300/2024/01244 | Centro | auxiliares | 266 | pendiente de revisar | — |
| 300/2024/00069 | Centro | limpieza | 2.657 | reparto leído del pliego | 77 % |
| 300/2024/00883 | Centro | mantenimiento | 475 | pendiente de revisar | — |
| 300/2025/02784 | Centro | seguridad | 468 | pendiente de revisar | — |
| 300/2024/00532 | Chamartin | auxiliares. limpieza. mantenimiento | 2.746 | reparto leído del pliego | 92 % |
| 300/2023/00800 | Chamartin | seguridad | 440 | pendiente de revisar | — |
| 300/2023/00053 | Chamberi | auxiliares | 611 | pendiente de revisar | — |
| 300/2024/00851 | Chamberi | limpieza | 1.864 | reparto leído del pliego | 69 % |
| 300/2024/00502 | Chamberi | seguridad | 85 | pendiente de revisar | — |
| 300/2024/00542 | Ciudad Lineal | auxiliares | 672 | pendiente de revisar | — |
| 300/2024/01171 | Ciudad Lineal | limpieza | 1.496 | reparto leído del pliego | 69 % |
| 300/2025/02711 | Ciudad Lineal | seguridad | 729 | pendiente de revisar | — |
| 300/2025/01604 | Fuencarral-El Pardo | auxiliares | 884 | pendiente de revisar | — |
| 300/2025/00239 | Fuencarral-El Pardo | limpieza | 4.709 | reparto leído del pliego | 77 % |
| 300/2024/00473 | Fuencarral-El Pardo | mantenimiento | 2.117 | reparto leído del pliego | 68 % |
| 300/2023/00292 | Fuencarral-El Pardo | seguridad | 402 | pendiente de revisar | — |
| 300/2024/00672 | Hortaleza | limpieza | 1.464 | pendiente de revisar | — |
| 300/2024/00912 | Hortaleza | mantenimiento | 2.072 | reparto leído del pliego | 88 % |
| 300/2023/00119 | Latina | auxiliares | 756 | pendiente de revisar | — |
| 300/2024/01123 | Latina | limpieza | 4.279 | reparto leído del pliego | 87 % |
| 300/2025/02724 | Latina | mantenimiento | 2.475 | reparto leído del pliego | 93 % |
| 300/2025/00789 | Moncloa-Aravaca | auxiliares | 534 | pendiente de revisar | — |
| 300/2024/00204 | Moncloa-Aravaca | mantenimiento | 1.411 | pendiente de revisar | — |
| 300/2023/00530 | Moncloa-Aravaca | seguridad | 996 | pendiente de revisar | — |
| 300/2025/04075 | Moratalaz | auxiliares | 266 | pendiente de revisar | — |
| 300/2025/01510 | Moratalaz | limpieza | 1.977 | reparto leído del pliego | 57 % |
| 300/2023/00673 | Moratalaz | seguridad | 343 | pendiente de revisar | — |
| 300/2025/01962 | Moratalaz | seguridad | 110 | pendiente de revisar | — |
| 300/2025/01892 | Retiro | auxiliares | 569 | pendiente de revisar | — |
| 300/2024/01270 | Retiro | limpieza | 2.258 | reparto leído del pliego | 71 % |
| 103/2026/00562 | Retiro | mantenimiento | 637 | sin reparto: contrato de emergencia sin pliego publicado | — |
| 300/2024/01118 | Retiro | seguridad | 632 | pendiente de revisar | — |
| 300/2022/00230 | Salamanca | auxiliares | 561 | pendiente de revisar | — |
| 300/2024/00154 | Salamanca | limpieza | 1.178 | pendiente de revisar | — |
| 300/2022/00730 | Salamanca | mantenimiento | 344 | pendiente de revisar | — |
| 300/2024/00400 | Salamanca | seguridad | 626 | pendiente de revisar | — |
| 300/2024/00566 | San Blas-Canillejas | auxiliares | 712 | pendiente de revisar | — |
| 300/2024/01392 | San Blas-Canillejas | limpieza | 4.701 | reparto leído del pliego | 78 % |
| 300/2025/01453 | San Blas-Canillejas | mantenimiento | 2.942 | reparto leído del pliego | 72 % |
| 300/2022/00493 | San Blas-Canillejas | seguridad | 691 | pendiente de revisar | — |
| 300/2022/00589 | Tetuan | limpieza | 1.922 | reparto leído del pliego | 89 % |
| 300/2024/00276 | Tetuan | seguridad | 871 | pendiente de revisar | — |
| 300/2021/00577 | Usera | auxiliares | 453 | pendiente de revisar | — |
| 300/2024/00663 | Usera | limpieza | 3.353 | reparto leído del pliego | 81 % |
| 300/2024/01096 | Usera | seguridad | 653 | pendiente de revisar | — |
| 300/2025/02455 | Vicalvaro | limpieza | 2.562 | reparto leído del pliego | 99 % |
| 300/2024/00266 | Vicalvaro | mantenimiento | 1.141 | reparto leído del pliego | 99 % |
| 300/2023/00023 | Vicalvaro | seguridad | 991 | pendiente de revisar | — |
| 300/2025/02656 | Villa De Vallecas | auxiliares | 739 | pendiente de revisar | — |
| 300/2024/00389 | Villa De Vallecas | limpieza | 3.533 | reparto leído del pliego | 97 % |
| 300/2024/00033 | Villa De Vallecas | mantenimiento | 829 | reparto leído del pliego | 75 % |
| 300/2023/00275 | Villa De Vallecas | seguridad | 803 | pendiente de revisar | — |
| 300/2022/00327 | Villaverde | auxiliares | 254 | pendiente de revisar | — |
| 300/2025/01011 | Villaverde | limpieza | 4.880 | reparto leído del pliego | 83 % |
| 300/2025/01650 | Villaverde | mantenimiento | 1.264 | reparto leído del pliego | 69 % |
| 300/2025/00055 | Villaverde | seguridad | 309 | pendiente de revisar | — |

Recuento: 40 pendiente de revisar, 24 reparto leído del pliego, 1 escaneado, 1 sin reparto
