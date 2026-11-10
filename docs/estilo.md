# Guía de estilo de la web

Reglas comunes para que todo lo que se añada se lea y se use igual. El consejo de revisión (`docs/consejo-revision.md`) comprueba que se cumplen.

## Lenguaje

- Español de España, lenguaje llano. Primero la respuesta en una frase («Este edificio ha recibido más inversión que 9 de cada 10 colegios de Madrid»), después el detalle.
- Sin siglas sin explicar la primera vez (ITE, IEE, IVTA, p.p.). Sin jerga contable («obligaciones reconocidas» → «pagado»).
- Las cifras llevan siempre unidad, periodo y fuente cerca («pagado 2014–2025, ejecución presupuestaria»).
- Las estimaciones se dicen como estimaciones, y lo que no se sabe se dice («no consta»), nunca se rellena.

## Comparaciones

- Una comparación responde a una pregunta explícita («¿Recibe más o menos que otros distritos con su población?»), con la referencia nombrada («media de los 21 distritos», «Madrid»).
- Se comparan magnitudes comparables: totales con totales por distrito, tasas con tasas; si el tamaño importa, por habitante o por edificio.
- Colores neutros para «más / menos» (no verde = bueno, rojo = malo), salvo el estado de la ITE, que sí tiene semáforo.
- Diferencias de porcentajes en puntos; de años, en años.
- Avisos de interpretación junto al dato, no solo al pie.

## Visual

- Colores de estado de la ITE: los de `STATES` en `index.html`. Azul `#1f5fa8` para lo seleccionado o principal, gris `#b8c2cc` para la referencia.
- Gráficos en SVG propios (`barChart`, `ganttChart`, `scatter`) con texto mínimo de 13 px a tamaño real, leyenda y título que diga qué se mide.
- Tarjetas (`.card`, `.kpi`) con: cifra grande, qué es, y comparación en una línea.
- Botón principal azul (`.btn.primary`), secundarios blancos.
- Móvil primero: nada que obligue a desplazar en horizontal sin indicarlo; zonas táctiles de 44 px.

- Mapas de distritos (coropletas): 5 azules secuenciales `CHB` (`#dbe7f3` → `#174a8a`), más oscuro = más valor, en 5 grupos por orden (unos 4 distritos cada uno). Excepción al azul de selección: el distrito elegido lleva borde naranja `#e8590c`, porque sobre azul no se distinguiría. Encima, la frase con valor, puesto y media de los 21 distritos; etiquetas en HTML a tamaño real (seleccionado y extremos); fuente y filtros activos al pie; enlace a la tabla como alternativa accesible.

## Navegación

- Cada vista y cada estado (distrito, filtros) tiene enlace propio y se puede compartir.
- Desde cualquier cifra de un edificio se llega a su ficha completa, y desde la ficha a la fuente.
- «Volver» devuelve a donde se estaba.
