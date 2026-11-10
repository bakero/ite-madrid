# Consejo de revisión

Todo lo que se añada o cambie en la web pasa por este consejo antes de publicarse. Cada miembro es un agente que revisa la web en su papel y entrega propuestas concretas. Después se aplican los cambios y el consejo comprueba el resultado en una segunda vuelta corta.

## Miembros

| Papel | Qué busca | Dispositivo |
|---|---|---|
| **Vecina de a pie** (68 años, poco técnica) | Encontrar su colegio o centro, entender en una frase si está bien, quién lo cuida y cuánto se ha invertido | Móvil 390×844 |
| **Técnico municipal** (arquitecto de mantenimiento) | Priorizar intervenciones, datos exactos y trazables, exportar, comparar con edificios del mismo tipo | Ordenador 1440×900 |
| **Concejal o vocal de Junta** y su asesor | Situación del distrito frente a Madrid y otros distritos, cifras citables con fuente, neutralidad, informe imprimible | Ordenador y tableta |
| **Asociación vecinal y periodista de datos** | Compartir, verificar cada cifra en su fuente, descargar, detectar sesgos y comparaciones engañosas | Móvil y ordenador |
| **Arquitecto de información, UX y accesibilidad** | Navegación, jerarquía, coherencia entre vistas, WCAG 2.1 AA, rendimiento | Ordenador y móvil |
| **Diseñador de información** (visualización de datos y lenguaje llano) | Que cada gráfico y cada comparación se entienda sin leer la ayuda, con el mismo estilo en toda la web | Ordenador y móvil |
| **Experto en producto** | Para quién es la web y qué tarea resuelve; enfoque «la información de mi distrito»; qué datos faltan, cómo organizar la aplicación y en qué orden construir | Todos |

## Cómo se revisa

- La web se sirve en local (`cd app && python3 -m http.server 8765`) y se recorre con Playwright como lo haría cada perfil, con capturas que se miran de verdad.
- Cada miembro lee antes `docs/estilo.md` y señala lo que no lo cumple.
- Entrega: los problemas más importantes ordenados por gravedad, cada uno con dónde ocurre, qué le pasa al usuario y un arreglo concreto; lo que funciona y no hay que tocar.
- Nadie modifica el repositorio durante la revisión: los cambios se hacen después, con todas las propuestas cruzadas.
- Segunda vuelta: el consejo comprueba solo lo cambiado y confirma o pide ajustes.
