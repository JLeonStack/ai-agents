# Contrato de agente: resumen semanal de un repo

## Qué construí

Un contrato completo (system prompt + user prompt) para un agente que convierte el `git log` crudo de un repo en un resumen semanal estructurado, listo para pegar en un status report. Es para mí como tech lead: hoy armo ese resumen a mano cada semana, y quiero que el output de cada repo se pueda comparar/pegar sin reformatear nada.

## Cómo se lo pedí

La consigna de la materia, tal cual:

> Elegí una tarea recurrente [...] y escribile el contrato completo para que un agente la haga por vos: un system prompt (identidad, reglas, formato por defecto) y un user prompt (el pedido puntual), cubriendo las seis piezas vistas en clase: rol, contexto, tarea, restricciones, formato y ejemplos. [...] Corrélo tres veces con casos reales y documentá dos iteraciones de mejora: qué falló (textual, no "quedó raro"), qué pieza del contrato tocaste, y qué cambió en la salida. Una pieza por vez.

A partir de ahí, mis pasos fueron:

1. "Necesito completar esta tarea [pega la consigna completa]. Ayudame a pensar una idea, y hacer cada una de las cosas."
2. Yo mismo elegí la idea (resumen semanal de repo) y armé `system_prompt.md` v1 con las seis piezas, pero con el formato de salida suelto ("Devolvé un resumen claro y organizado por categoría").
3. Lo corrí contra el `git log` real de `meli-challenge` — falló (ver abajo). Ajusté solo la pieza de Formato.
4. Lo corrí contra el `git log` real de `JLeonStack` — falló distinto. Ajusté Tarea y Restricciones.
5. Lo corrí contra `jacaris` con el contrato ya corregido — anduvo.
6. "Antes [de pushear], hacé que el texto del README no parezca machine-like sino human-like." — reescribí el README en primera persona, tono conversacional.
7. "Reorganizá los proyectos, que queden en carpetas separadas, hoy está todo mezclado." — moví VozBar a su propia carpeta `vozbar/` para que esta entrega no quedara mezclada en la raíz del repo.
8. "El README del proyecto desarrollado debería tener esta estructura [pega el template estándar de la materia]." — reescribí este README con las secciones Qué construí / Cómo se lo pedí / Qué funciona / Qué falta o qué falló / Qué aprendí.

## Qué funciona

- El contrato final (`system_prompt.md` + `user_prompt.md`) produce JSON válido y parseable en las tres corridas, con el mismo schema exacto: `repo`, `period_note`, `total_commits`, `by_category`, `commits[]`, `executive_summary`, `risks`.
- Las categorías (`feat`, `fix`, `refactor`, `docs`, `chore`, `otros`) salen siempre de esa lista cerrada — lo verifiqué en las 15 commits de la corrida final sobre `jacaris`, ninguno se sale del enum.
- El agente detecta riesgos reales del log sin que se los pida explícitamente por caso (hueco de meses entre commits, mensaje de una sola palabra, muchos commits el mismo día sobre lo mismo).
- Las tres corridas usaron `git log` real de tres repos míos (`meli-challenge`, `JLeonStack`, `jacaris`), sin inventar ningún commit — quedaron en [`runs/`](runs/).

## Qué falta o qué falló

- **Corrida 1 (contrato v1, sobre `meli-challenge`):** el agente devolvió prosa con títulos en Markdown ("Documentación", "Mejoras / Backend") en vez de datos estructurados, con categorías inventadas al vuelo y un commit de README listado dos veces sin marcarlo. Ver [`runs/run1_output.txt`](runs/run1_output.txt). Causa: la sección Formato de salida no tenía schema, solo decía "resumen claro y organizado".
- **Corrida 2 (contrato v2, sobre `JLeonStack`):** ya devolvía JSON válido, pero frente a commits sin prefijo tipo Conventional Commits ("Delete", "update profile", "Initial commit") el agente se inventó una categoría nueva fuera del schema, `"misc"` — aparece en `by_category.misc` y en tres `commits[].category`. Ver [`runs/run2_output.json`](runs/run2_output.json). Causa: la Tarea decía "clasificá por categoría" sin lista cerrada ni regla para el caso sin prefijo.
- No probé el caso de un log vacío ni un log con miles de commits (posible problema de tamaño de contexto si el repo tiene mucha actividad en la semana) — quedó afuera del alcance de esta entrega.

## Qué aprendí

El contrato no se rompe por instrucciones vagas en general — se rompe en el borde, con el input real que no sigue la convención que yo tenía en la cabeza (el commit sin prefijo, el mensaje repetido, el hueco de meses). Cada falla la disparó un caso real, no una relectura del prompt. Tocar una sola pieza por vez ayudó a que quedara claro qué arregló qué: si hubiera reescrito todo de una, no sabría si el fix fue el schema o la regla de categorías. Y la categoría `misc` inventada en la corrida 2 me dejó algo grabado: sin restricción cerrada, el modelo siempre encuentra una salida "razonable" para el caso ambiguo, y esa salida no es predecible de antemano — por eso el enum cerrado no es un detalle prolijo, es lo que hace que el output sirva para comparar entre corridas.

¿No sabés crear el repositorio? Pedíselo a tu tutor IA, literalmente así:

Soy principiante. Quiero crear un repositorio público en GitHub desde el navegador,
subir mis archivos y un README, sin usar la terminal. Guiame paso a paso,
uno por vez, y esperá mi confirmación antes de seguir.
