# Reparto por edificio de los servicios de las Juntas (fuera de Puente de Vallecas)

Estado a 11/11/2026: 13 con reparto leído del pliego, 52 pendientes de revisar, 1 escaneado (sin texto), 1 contrato de emergencia sin pliego.

Método (`scripts/servicios/reparto_pliegos.py`): se lee la tabla del pliego que da el peso de cada edificio —m² construidos en limpieza y mantenimiento, horas de limpieza al año si el pliego las da— y el importe del lote se reparte en proporción. Las filas que no se reconocen como edificio del mapa cuentan en el total del lote. Las asignaciones dudosas revisadas a mano se anulan en `datos/servicios/reparto_pliegos_cfg.json` (`anular`).

Pendiente: seguridad y servicios auxiliares (el peso son horas o puestos, en tablas de formato muy variable), contratos de limpieza con tablas de horas por trabajador (como Centro) y pliegos escaneados (necesitan OCR).

| Expediente | Distrito | Servicios | Miles €/año | Estado |
|---|---|---|---:|---|
| 300/2022/00401 | Arganzuela | auxiliares | 588 | pendiente de revisar |
| 300/2024/00418 | Arganzuela | limpieza. mantenimiento | 3.138 | pendiente de revisar |
| 300/2023/00396 | Arganzuela | seguridad | 1.260 | pendiente de revisar |
| 300/2024/01423 | Barajas | limpieza | 370 | escaneado (sin texto) |
| 300/2025/02814 | Barajas | limpieza | 656 | pendiente de revisar |
| 300/2025/00468 | Barajas | mantenimiento | 635 | pendiente de revisar |
| 300/2023/00196 | Carabanchel | auxiliares | 1.181 | pendiente de revisar |
| 300/2024/00101 | Carabanchel | limpieza | 5.105 | reparto leído del pliego |
| 300/2024/00679 | Carabanchel | mantenimiento | 1.257 | reparto leído del pliego |
| 300/2024/01321 | Carabanchel | seguridad | 822 | pendiente de revisar |
| 300/2024/01244 | Centro | auxiliares | 266 | pendiente de revisar |
| 300/2024/00069 | Centro | limpieza | 2.657 | reparto leído del pliego |
| 300/2024/00883 | Centro | mantenimiento | 475 | pendiente de revisar |
| 300/2025/02784 | Centro | seguridad | 468 | pendiente de revisar |
| 300/2024/00532 | Chamartin | auxiliares. limpieza. mantenimiento | 2.746 | pendiente de revisar |
| 300/2023/00800 | Chamartin | seguridad | 440 | pendiente de revisar |
| 300/2023/00053 | Chamberi | auxiliares | 611 | pendiente de revisar |
| 300/2024/00851 | Chamberi | limpieza | 1.864 | reparto leído del pliego |
| 300/2024/00502 | Chamberi | seguridad | 85 | pendiente de revisar |
| 300/2024/00542 | Ciudad Lineal | auxiliares | 672 | pendiente de revisar |
| 300/2024/01171 | Ciudad Lineal | limpieza (tabla de horas irregular: revisar a mano) | 1.496 | pendiente de revisar |
| 300/2025/02711 | Ciudad Lineal | seguridad | 729 | pendiente de revisar |
| 300/2025/01604 | Fuencarral-El Pardo | auxiliares | 884 | pendiente de revisar |
| 300/2025/00239 | Fuencarral-El Pardo | limpieza | 4.709 | reparto leído del pliego |
| 300/2024/00473 | Fuencarral-El Pardo | mantenimiento | 2.117 | reparto leído del pliego |
| 300/2023/00292 | Fuencarral-El Pardo | seguridad | 402 | pendiente de revisar |
| 300/2024/00672 | Hortaleza | limpieza | 1.464 | pendiente de revisar |
| 300/2024/00912 | Hortaleza | mantenimiento | 2.072 | pendiente de revisar |
| 300/2023/00119 | Latina | auxiliares | 756 | pendiente de revisar |
| 300/2024/01123 | Latina | limpieza | 4.279 | pendiente de revisar |
| 300/2025/02724 | Latina | mantenimiento | 2.475 | reparto leído del pliego |
| 300/2025/00789 | Moncloa-Aravaca | auxiliares | 534 | pendiente de revisar |
| 300/2024/00204 | Moncloa-Aravaca | mantenimiento | 1.411 | pendiente de revisar |
| 300/2023/00530 | Moncloa-Aravaca | seguridad | 996 | pendiente de revisar |
| 300/2025/04075 | Moratalaz | auxiliares | 266 | pendiente de revisar |
| 300/2025/01510 | Moratalaz | limpieza | 1.977 | reparto leído del pliego |
| 300/2023/00673 | Moratalaz | seguridad | 343 | pendiente de revisar |
| 300/2025/01962 | Moratalaz | seguridad | 110 | pendiente de revisar |
| 300/2025/01892 | Retiro | auxiliares | 569 | pendiente de revisar |
| 300/2024/01270 | Retiro | limpieza | 2.258 | pendiente de revisar |
| 103/2026/00562 | Retiro | mantenimiento | 637 | contrato de emergencia: sin pliego publicado |
| 300/2024/01118 | Retiro | seguridad | 632 | pendiente de revisar |
| 300/2022/00230 | Salamanca | auxiliares | 561 | pendiente de revisar |
| 300/2024/00154 | Salamanca | limpieza | 1.178 | pendiente de revisar |
| 300/2022/00730 | Salamanca | mantenimiento | 344 | pendiente de revisar |
| 300/2024/00400 | Salamanca | seguridad | 626 | pendiente de revisar |
| 300/2024/00566 | San Blas-Canillejas | auxiliares | 712 | pendiente de revisar |
| 300/2024/01392 | San Blas-Canillejas | limpieza | 4.701 | pendiente de revisar |
| 300/2025/01453 | San Blas-Canillejas | mantenimiento | 2.942 | pendiente de revisar |
| 300/2022/00493 | San Blas-Canillejas | seguridad | 691 | pendiente de revisar |
| 300/2022/00589 | Tetuan | limpieza | 1.922 | pendiente de revisar |
| 300/2018/00448 | Tetuan | mantenimiento | 2.621 | pendiente de revisar (contrato integral 2018, pliego de 108 págs.) |
| 300/2024/00276 | Tetuan | seguridad | 871 | pendiente de revisar |
| 300/2021/00577 | Usera | auxiliares | 453 | pendiente de revisar |
| 300/2024/00663 | Usera | limpieza | 3.353 | pendiente de revisar |
| 300/2024/01096 | Usera | seguridad | 653 | pendiente de revisar |
| 300/2025/02455 | Vicalvaro | limpieza | 2.562 | reparto leído del pliego |
| 300/2024/00266 | Vicalvaro | mantenimiento | 1.141 | reparto leído del pliego |
| 300/2023/00023 | Vicalvaro | seguridad | 991 | pendiente de revisar |
| 300/2025/02656 | Villa De Vallecas | auxiliares | 739 | pendiente de revisar |
| 300/2024/00389 | Villa De Vallecas | limpieza | 3.533 | pendiente de revisar |
| 300/2024/00033 | Villa De Vallecas | mantenimiento | 829 | reparto leído del pliego |
| 300/2023/00275 | Villa De Vallecas | seguridad | 803 | pendiente de revisar |
| 300/2022/00327 | Villaverde | auxiliares | 254 | pendiente de revisar |
| 300/2025/01011 | Villaverde | limpieza | 4.880 | reparto leído del pliego |
| 300/2025/01650 | Villaverde | mantenimiento | 1.264 | reparto leído del pliego |
| 300/2025/00055 | Villaverde | seguridad | 309 | pendiente de revisar |
