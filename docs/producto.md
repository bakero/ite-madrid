# Propuesta de producto: «Mi distrito»

Estado: **fase «Ahora» publicada el 11/11/2026** (carga diferida, distrito común con `?d=`, vista Mi distrito, comparativas rediseñadas). Pendiente: decisiones 4 y 5, pliegos de los 20 distritos, partir `data.js` por distrito (la primera carga sigue siendo ~3,3 MB sin comprimir, ~0,6 MB comprimida). Redactada por el Experto en producto del consejo (docs/consejo-revision.md).

## Propuesta de valor
«Cómo están, quién cuida y cuánto se invierte en los edificios públicos de tu distrito, comparado con Madrid, con cada cifra enlazada a su fuente oficial.»

| Usuario | Tareas clave |
|---|---|
| Vecina (móvil) | Encontrar su edificio por nombre o dirección y saber en una frase si está bien; quién lo limpia o mantiene; avisar de un error |
| Técnico municipal | Lista priorizada del distrito; comparar con edificios del mismo tipo; exportar con identificadores trazables |
| Concejal / vocal | «Mi distrito frente a Madrid» citable; PDF para el pleno; evolución en el tiempo |
| Asociación vecinal | Argumentos para reclamar; enlaces para compartir |
| Periodista de datos | Comparación neutral de los 21 distritos; descarga completa; cobertura desigual visible |

## Arquitectura de información
- **Entrada `#/`**: mapa de los 21 distritos, buscador único (distrito, barrio, edificio, dirección) y «Usar mi ubicación». El distrito elegido se recuerda.
- **Resumen `#/d/{cod}`**: frase resumen; 4 KPIs con comparación (% desfavorable, inversión €/hab., servicios €/año, sin ITE); mapa del distrito; lo urgente (5 filas); contexto socioeconómico plegado; compartir/PDF/CSV.
- **Barra fija** con selector de distrito; pestañas Resumen · Edificios · Prioridades · Inversión · Servicios · Informe. Fuera: Comparar distritos, Ayuda y datos.

| Vista actual | Destino |
|---|---|
| mapa | «Edificios» del distrito (mapa/lista) |
| urgente | «Prioridades» del distrito; todo Madrid dentro de Comparar |
| panel (Cifras) | KPIs a Resumen; tabla y segmentador a Comparar; desaparece |
| inversion | Tabla 21 y dispersión a Comparar; año, tipo y top a «Inversión»; servicios y empresas a «Servicios» |
| informe | Acción del distrito con ámbito ya elegido |
| ficha | Se mantiene, con miga de pan |
| ayuda | Se mantiene, con «Cobertura por distrito» |

Rutas: `#/`, `#/d/{cod}`, `#/d/{cod}/edificios|prioridades|inversion|servicios|informe`, `#/d/{cod}/b/{barrio}`, `#/edificio/{lat,lng}`, `#/comparar?ind=…`, `#/cerca?q=…`, `#/ayuda`. Redirecciones desde `#mapa`, `#edificio=`, `#ficha=`, `#inversion?d=`.

## Huecos de datos (identificadores sin verificar)
Presupuesto y ejecución por Junta; avisos Línea Madrid 010; equipamientos completos; licencias urbanísticas; calidad del aire y ruido; presupuestos participativos; actas de plenos de Junta; contratos menores de mantenimiento ya ingeridos a una pestaña Servicios; BOE 1995–2014 en los otros 20 distritos; serie temporal de la ITE; padrón por barrio y edad.

## Roadmap
- **Ahora**: router `#/d/{cod}/…` con estado único de distrito; entrada y Resumen; recolocar vistas; avisos de cobertura por distrito; datos en JSON por distrito cargados bajo demanda (objetivo < 500 KB en la primera visita frente a ~9 MB hoy).
- **Siguiente**: módulos ES sin bundler; PDF «para el pleno»; Comparar distritos unificado; serie temporal ITE; equipamientos y presupuesto por Junta; CSV por pestaña.
- **Después**: resumen por barrio; 010, participativos, aire; BOE en 21 distritos; avisos de cambios; actualización con GitHub Actions.

## Riesgos
Lectura como ranking; cobertura mayor en Puente de Vallecas que infla sus cifras; ITE tomada por certificado oficial; Registro manual; romper enlaces compartidos.

## Decisiones del dueño
1. ¿La entrada obliga a elegir distrito o el mapa de todo Madrid sigue siendo la portada? **Decidido (11/11/2026): el mapa de todo Madrid sigue de portada, con un botón destacado para elegir distrito.**
2. ¿Datos en JSON por distrito con `fetch` (deja de funcionar abriendo `index.html` sin servidor)? **Decidido (11/11/2026): sí, datos por distrito con carga bajo demanda.**
3. ¿Servicios por edificio en los 20 distritos sin pliego verificado, marcados como estimación, o solo coste del contrato completo? **Decidido (11/11/2026): hacer la misma investigación de pliegos que en Puente de Vallecas en los otros 20 distritos, después de los cambios de la aplicación.**
4. ¿Prioridad siguiente: uso institucional o ciudadano? **Decidido (11/11/2026): los dos por igual.**
5. ¿Fuentes de riesgo alto (010, participativos) en esta versión o solo datos trazables por edificio? **Decidido (11/11/2026): primero comprobar que existen en datos.madrid.es y con qué calidad; decidir después.**
