# Contrato de agente: resumen semanal de un repo

## Qué construí

La tarea que elegí es una que hago (o debería hacer) todas las semanas: abrir el `git log` de cada repo activo y armar el resumen para el status report. Es repetitiva, siempre sigue la misma lógica, y necesito que el resultado se pueda pegar junto con el de otros repos sin tener que reacomodar nada a mano. Así que en vez de pedírselo suelto cada vez, le escribí el contrato completo a un agente: `system_prompt.md` con su identidad fija y `user_prompt.md` con el pedido puntual (la plantilla que voy a reusar cada semana, cambiando solo el repo, el período y el log pegado).

Las seis piezas que vimos en clase están ahí, separadas por sección: Rol, Contexto, Tarea, Restricciones, Formato de salida, Ejemplos.

## Cómo lo probé

Corrí el contrato tres veces, con `git log` real de tres repos míos —nada inventado—:

- **`meli-challenge`**: log prolijo, muchos commits de README y del sistema de memoria del bot. El caso "fácil" para arrancar.
- **`JLeonStack`**: mi propio perfil de GitHub. Log sucio a propósito: commits sin prefijo tipo `Delete` o `update profile`, y un hueco de nueve meses entre dos commits. Lo elegí porque sabía que iba a romper algo.
- **`jacaris`**: un side project con Conventional Commits reales (`feat(x):`, `chore(x):`). Es el caso que usé para la corrida final, con el contrato ya corregido.

Los tres outputs quedaron guardados en [`runs/`](runs/).

## Primera iteración

Arranqué con un `system_prompt` bastante flojo en la parte de formato. Literal decía:

> Devolvé un resumen claro y organizado por categoría.

Nada de JSON, nada de lista cerrada de categorías.

En la primera corrida, sobre `meli-challenge`, el agente me devolvió esto (ver [`runs/run1_output.txt`](runs/run1_output.txt)): prosa con títulos en Markdown como "Documentación" y "Mejoras / Backend", categorías que se inventó en el momento, y hasta un commit de README que listó dos veces sin avisar. No servía para nada: no lo podía comparar con la corrida de otro repo ni pegarlo en una tabla.

Ahí toqué solo la pieza de **Formato de salida**: le puse un schema de JSON fijo, con los campos que necesito (`repo`, `by_category`, `commits[]`, etc.) y la aclaración de que no quiero backticks ni texto alrededor. Con eso, la segunda corrida ya me devolvió JSON parseable.

## Segunda iteración

El JSON ya estaba bien armado, pero la **Tarea** todavía decía nomás "clasificá cada commit por categoría", sin especificar qué categorías existen ni qué hacer con un mensaje que no tiene prefijo.

Ahí es donde `JLeonStack` cumplió su función de caso trampa. El log tiene commits como "Delete", "update profile" e "Initial commit", sin ningún `feat:`/`fix:` que los guíe. El agente, al no tener una lista cerrada, se inventó una categoría nueva: `misc` (podés verla en [`runs/run2_output.json`](runs/run2_output.json), tanto en `by_category.misc` como en tres de los commits). Es exactamente el tipo de cosa que rompe la comparación entre corridas: la corrida anterior no tenía esa clave, así que ya no calzan.

Para esta, toqué la **Tarea** y las **Restricciones**: agregué la lista cerrada de categorías (`feat`, `fix`, `refactor`, `docs`, `chore`, `otros`) y la regla de qué hacer si el mensaje no trae prefijo —inferir por contenido, y si no se puede, usar `otros`, nunca inventar algo nuevo—.

Con eso corrí la tercera vez sobre `jacaris`: los 15 commits quedaron clasificados sin salirse nunca de esas seis categorías. Está en [`runs/run3_output.json`](runs/run3_output.json).

## Qué aprendí

Lo que más me sorprendió es que el contrato no se rompe por instrucciones vagas en general —"sé claro", "organizá bien"— sino en el borde concreto, con el input real que no sigue la convención que yo tenía en la cabeza. El commit sin prefijo, el mensaje repetido, el hueco de meses: cada falla la disparó un caso real, no una relectura del prompt sentado en el escritorio. Y cambiar una sola pieza por vez ayudó a que quede clarísimo qué arregló qué —si hubiera reescrito todo el contrato de una, no sabría si el fix fue el schema o la regla de categorías—.

La categoría `misc` inventada en la segunda corrida es el ejemplo que más me quedó grabado: sin una restricción cerrada, el modelo siempre va a encontrar una salida "razonable" para el caso ambiguo, y esa salida no es predecible de antemano. Por eso, si el output se va a comparar entre corridas, el enum cerrado no es un detalle prolijo: es lo que hace que el contrato sirva.
