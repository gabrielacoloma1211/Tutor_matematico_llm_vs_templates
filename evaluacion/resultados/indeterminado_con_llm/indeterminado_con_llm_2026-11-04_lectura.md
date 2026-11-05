# El LLM llamado en casos indeterminados: hoja de lectura

Para cada caso marca: (a) la pista inventa una causa que no es la real; (b) menciona solo uno de los errores; (c) es honesta y no afirma una causa; (d) revela la solución; (e) acierta.

## DEV-089 (dev)
- Ejercicio: Resuelve: 2x - 1 = 6 + x
- Paso anterior: `2x - 1 = 6 + x`
- Paso del estudiante: `2x + x = 6 - 1`
- Lo que realmente pasó: Combinado = dos errores de signo en un mismo paso.
- Pista del LLM: Revisa con calma cada parte de tu paso y compáralo con el anterior. Tómate tu tiempo para verificar que cada término esté escrito correctamente. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-090 (dev)
- Ejercicio: Resuelve: x/2 + 7x/2 = 4 + 3
- Paso anterior: `8x/2 = 7`
- Paso del estudiante: `8x = 7/2`
- Lo que realmente pasó: No encaja: multiplica al lado izquierdo y divide en el derecho.
- Pista del LLM: Revisa con calma este paso. Compara lo que tenías con lo que escribiste y verifica que cada parte cambió como debía. Tómate tu tiempo, vas por buen camino.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-091 (dev)
- Ejercicio: Resuelve: 3x/2 + 12 = 9
- Paso anterior: `3x/2 = -3`
- Paso del estudiante: `3x = -3/2`
- Lo que realmente pasó: No encaja: multiplica al lado izquierdo y divide en el derecho
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior. Fíjate bien en cada operación y en si la igualdad se mantiene. Tómate tu tiempo, tú puedes encontrar el error.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-092 (dev)
- Ejercicio: Resuelve: 4x/3 + 13 = 2 + 8
- Paso anterior: `4x/3 = -3`
- Paso del estudiante: `4x = -3/3`
- Lo que realmente pasó: No encaja: multiplica al lado izquierdo y divide en el derecho
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior, línea por línea. A veces un detalle pequeño cambia todo el resultado. Tómate tu tiempo, sé que lo encontrarás si lo lees con atención.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-093 (dev)
- Ejercicio: Resuelve: 4x + 6 = 2x - 3 + 17
- Paso anterior: `4x + 6 = 2x - 3 + 17`
- Paso del estudiante: `4x + 2x = -3 + 17 + 6`
- Lo que realmente pasó: Combinado = dos errores de signo en un mismo paso
- Pista del LLM: Vuelve al paso anterior y compara con calma cada término de este paso con su equivalente en la ecuación de arriba. Tómate tu tiempo, vas por buen camino y revisar así es una gran forma de aprender.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-094 (dev)
- Ejercicio: Resuelve: x/2 + 2x + 7 = 19
- Paso anterior: `x + 4x + 14 = 38`
- Paso del estudiante: `4x = 38 + 14`
- Lo que realmente pasó: Combinado = error de cálculo y de signo en un mismo paso
- Pista del LLM: Revisa con calma el paso que hiciste al mover el 14 al otro lado de la igualdad. Compara cada número y cada operación con la ecuación anterior, y verifica que todo quedó como debía. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): signo
- Marca (a/b/c/d): b

## DEV-095 (dev)
- Ejercicio: Resuelve: 7x - 8/2 - 3x + 6 = 22
- Paso anterior: `7x - 4 - 3x + 6 = 22`
- Paso del estudiante: `6x = 22 + 4 + 6`
- Lo que realmente pasó: Combinado = error de cálculo y de signo en un mismo paso
- Pista del LLM: Revisa este paso con calma, comparándolo línea por línea con el anterior. Fíjate bien en cada signo y en cada número. No te apresures: revisar tu propio trabajo es una gran habilidad.
- Causas que nombra (automático): signo
- Marca (a/b/c/d): c

## DEV-096 (dev)
- Ejercicio: Resuelve: 7x - 2(x - 3) + 1 = 27
- Paso anterior: `7x - 2(x - 3) + 1 = 27`
- Paso del estudiante: `7x - 2x - 6 = 27 + 1`
- Lo que realmente pasó: Combinado = distributiva con signo equivocado.
- Pista del LLM: Revisa con calma este paso comparándolo con el anterior, parte por parte. Fíjate bien en cada cambio que hiciste al escribirlo. Confío en que lo encontrarás, ¡sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-097 (dev)
- Ejercicio: Resuelve: 6x - 5 + x/2 = 21
- Paso anterior: `6x - 5 + x/2 = 21`
- Paso del estudiante: `12x + x = 21 - 5`
- Lo que realmente pasó: Combinado = operación en un solo lado y error de signo en el mismo paso.
- Pista del LLM: Revisa con calma el paso que escribiste. Compara cada término de la ecuación anterior con el nuevo y fíjate si todo quedó tal como debía. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-098 (dev)
- Ejercicio: Resuelve: 7x - 2(x - 3) = 27
- Paso anterior: `7x - 2x = 27 - 6`
- Paso del estudiante: `4x = 20`
- Lo que realmente pasó: Combinado = dos errores de cálculo en el mismo paso.
- Pista del LLM: Revisa con calma este paso, comparando cada lado de la igualdad con el anterior. Fíjate bien en cada número y en cada operación que hiciste. ¡Tú puedes encontrar dónde está el detalle!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-099 (dev)
- Ejercicio: Resuelve: 6x + 5 - (x + 4) = 21
- Paso anterior: `5x = 20`
- Paso del estudiante: `x = 20 - 5`
- Lo que realmente pasó: No encaja: operación equivocada al despejar.
- Pista del LLM: Revisa con calma el paso que acabas de escribir. Compara la nueva ecuación con la anterior y fíjate si lo que hiciste con cada lado mantiene la igualdad. Tómate tu tiempo, tú puedes encontrarlo.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## DEV-100 (dev)
- Ejercicio: Resuelve: 9x - (3x + 5) = 25
- Paso anterior: `9x - 3x - 5 = 25`
- Paso del estudiante: `x = 25`
- Lo que realmente pasó: No encaja: suma términos que no son semejantes.
- Pista del LLM: Revisa con calma el paso que escribiste, comparándolo línea por línea con el anterior. Hazlo despacio y verifica cada cambio que hiciste. Equivocarse es parte de aprender, ¡tú puedes lograrlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-008 (ampliado)
- Ejercicio: Resuelve: 8 - 3(x - 2) = x + 4
- Paso anterior: `8 - 3(x - 2) = x + 4`
- Paso del estudiante: `5(x - 2) = x + 4`
- Lo que realmente pasó: Resta 8 - 3 antes de multiplicar el 3 por el paréntesis, sin respetar el orden de las operaciones.
- Pista del LLM: Revisa con calma cada parte de este paso y compáralo con el anterior, sin apuro. Si lo revisas con atención, seguro encuentras qué necesita corrección. ¡Tú puedes lograrlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-010 (ampliado)
- Ejercicio: Resuelve: 3x/2 = (x + 5)/4
- Paso anterior: `3x/2 = (x + 5)/4`
- Paso del estudiante: `3x = x + 5`
- Lo que realmente pasó: Multiplica el lado izquierdo por 2 y el derecho por 4, cada uno por su propio denominador.
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior, parte por parte. Vuelve a verificar cada operación que hiciste antes de escribirlo. Tú puedes encontrar qué ajustar, ¡sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-016 (ampliado)
- Ejercicio: Resuelve: 5x + 3 * 2 = 2x + 15
- Paso anterior: `5x - 2x = 15 - 3 * 2`
- Paso del estudiante: `3x = 12 * 2`
- Lo que realmente pasó: Calcula 15 - 3 antes de multiplicar por 2, sin respetar la prioridad de la multiplicación.
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior. Fíjate bien en cada operación que hiciste y en el resultado de cada lado de la igualdad. Tómate tu tiempo, seguro lo encuentras.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-017 (ampliado)
- Ejercicio: Resuelve: (2/3)x + 1 = 9
- Paso anterior: `(2/3)x = 8`
- Paso del estudiante: `x = 8 * 2/3`
- Lo que realmente pasó: Para despejar x multiplica por 2/3 en lugar de multiplicar por el recíproco 3/2. Mismo patrón que DEV-090/091: opera al revés en cada lado.
- Pista del LLM: Revisa con calma el paso que acabas de escribir y compáralo con la ecuación anterior. Fíjate bien en cada operación que hiciste y en cómo se relaciona con la ecuación original. Tómate tu tiempo, ¡tú puedes lograrlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-018 (ampliado)
- Ejercicio: Resuelve: 7x - 4 = 3x + 20
- Paso anterior: `4x = 24`
- Paso del estudiante: `x = 4/24`
- Lo que realmente pasó: Invierte la división y escribe el coeficiente 4 sobre 24 en lugar de 24 entre 4.
- Pista del LLM: Revisa con calma cómo pasaste de la primera línea a la segunda. Fíjate bien en cada número y en cada operación que usaste, y comprueba después si tu resultado tiene sentido con la ecuación original. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-020 (ampliado)
- Ejercicio: Resuelve: 2x/5 - 3 = 3
- Paso anterior: `2x/5 = 6`
- Paso del estudiante: `x = 6/2`
- Lo que realmente pasó: Divide entre 2 como si fuera el coeficiente, sin tener en cuenta que el coeficiente real es 2/5.
- Pista del LLM: Revisa con calma cómo pasaste del paso anterior a este. Fíjate bien en cada número y en cada operación que usaste, porque cualquier detalle puede cambiar el resultado. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-025 (ampliado)
- Ejercicio: Resuelve: 6x + 10 - 2x - 2 = 20
- Paso anterior: `4x + 8 = 20`
- Paso del estudiante: `4(x + 8) = 20`
- Lo que realmente pasó: Al sacar factor común 4 de 4x + 8 deja el 8 sin dividir y escribe 4(x + 8).
- Pista del LLM: Compara con cuidado el paso anterior con el que escribiste. Revisa cada parte de la expresión y comprueba que lo que hiciste siga siendo equivalente a la ecuación original. Tómate tu tiempo, vas por buen camino.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-029 (ampliado)
- Ejercicio: Resuelve: x/4 - 1 = 2 + x/2
- Paso anterior: `x/4 = 3 + x/2`
- Paso del estudiante: `x = 3 + 2x`
- Lo que realmente pasó: Multiplica por 4 los términos con fracción de ambos lados pero deja sin multiplicar el 3, que no tiene denominador.
- Pista del LLM: Revisa con calma este paso. Compara la ecuación anterior con la nueva, término por término, y verifica que cada cambio se haya hecho con cuidado. ¡Tú puedes encontrarlo, sigue intentando!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-031 (ampliado)
- Ejercicio: Resuelve: (x + 2)/5 = (x - 1)/2
- Paso anterior: `(x + 2)/5 = (x - 1)/2`
- Paso del estudiante: `5(x + 2) = 2(x - 1)`
- Lo que realmente pasó: Al multiplicar en cruz multiplica cada numerador por su propio denominador en vez de por el del otro lado.
- Pista del LLM: Revisa con calma cómo pasaste de la ecuación anterior a esta. Verifica cada parte de la transformación, porque puede haber más de un detalle por ajustar. Tómate tu tiempo: con una revisión cuidadosa seguro lo encontrarás.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-032 (ampliado)
- Ejercicio: Resuelve: 7x + 4 = 2x + 19
- Paso anterior: `7x + 4 = 2x + 19`
- Paso del estudiante: `7x + 4 - 2x = 2x + 19 - 2`
- Lo que realmente pasó: Resta 2x en el lado izquierdo pero en el lado derecho resta solo 2, sin la x.
- Pista del LLM: Revisa con calma este paso y piensa si lo que hiciste en cada lado de la igualdad mantiene la ecuación equivalente. Fíjate bien en cada término antes de seguir. ¡Tú puedes encontrar el detalle!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-035 (ampliado)
- Ejercicio: Resuelve: x/3 + 0.5 = 2
- Paso anterior: `x/3 + 0.5 = 2`
- Paso del estudiante: `x/3 + 1/5 = 2`
- Lo que realmente pasó: Convierte el decimal 0.5 en la fracción 1/5 en lugar de 5/10 = 1/2.
- Pista del LLM: Compara con calma la ecuación anterior con la que escribiste y revisa cada término. Fíjate si el cambio que hiciste en uno de ellos conserva el mismo valor. Tómate tu tiempo, vas por buen camino.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-049 (ampliado)
- Ejercicio: Resuelve: 2(x + 3) + 1 = 15
- Paso anterior: `2(x + 3) = 14`
- Paso del estudiante: `2(x + 3 - 3) = 14 - 3`
- Lo que realmente pasó: Resta 3 dentro del paréntesis, lo que equivale a restar 6 a la izquierda, pero al lado derecho solo le resta 3.
- Pista del LLM: Revisa con calma este paso y compáralo con el anterior, línea por línea. Fíjate bien en cada lado de la igualdad y en cada operación que realizaste. Tú puedes encontrar el detalle, ¡sigue intentando!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-050 (ampliado)
- Ejercicio: Resuelve: 2/3 = (x - 1)/6
- Paso anterior: `2/3 = (x - 1)/6`
- Paso del estudiante: `3/2 = (x - 1)/6`
- Lo que realmente pasó: Invierte la fracción 2/3 del lado izquierdo y deja igual el lado derecho.
- Pista del LLM: Revisa con calma el paso que acabas de escribir y compáralo con el anterior, fijándote bien en cada número y en cada signo. Tómate tu tiempo, a veces un detalle pequeño cambia todo el resultado. ¡Tú puedes hacerlo!
- Causas que nombra (automático): signo
- Marca (a/b/c/d): c

## AMP-051 (ampliado)
- Ejercicio: Resuelve: 0.25x + 2 = 3.5
- Paso anterior: `0.25x = 1.5`
- Paso del estudiante: `25x = 15`
- Lo que realmente pasó: Para quitar los puntos decimales multiplica el lado izquierdo por 100 y el derecho solo por 10.
- Pista del LLM: Revisa este paso con calma y compáralo línea por línea con el anterior. Lee cada número y cada cambio con atención, porque a veces un detalle pequeño se nos escapa. ¡Tú puedes volver a intentarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-052 (ampliado)
- Ejercicio: Resuelve: 8x + 6 = 6x + 16
- Paso anterior: `2x + 6 = 16`
- Paso del estudiante: `x + 6 = 8`
- Lo que realmente pasó: Divide entre 2 el término 2x y el lado derecho, pero deja el +6 sin dividir.
- Pista del LLM: Este paso no es correcto, pero revisarlo con calma te ayudará. Compara con cuidado la ecuación anterior con la nueva y fíjate bien en cómo cambió cada parte. ¡Tú puedes encontrar el error!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-053 (ampliado)
- Ejercicio: Resuelve: (1/2)x + 2 = 11/4
- Paso anterior: `x = (3/4)/(1/2)`
- Paso del estudiante: `x = 3/8`
- Lo que realmente pasó: Al dividir 3/4 entre 1/2 multiplica las fracciones en lugar de multiplicar por el recíproco 2/1.
- Pista del LLM: Revisa con calma el paso que acabas de escribir y compáralo con el anterior. Fíjate bien en cada número y en cada operación que hiciste. Tómate tu tiempo, ¡tú puedes encontrar el error!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-060 (ampliado)
- Ejercicio: Resuelve: 2x + 5 = x + 20
- Paso anterior: `x + 5 = 20`
- Paso del estudiante: `x = 20/5`
- Lo que realmente pasó: Divide entre 5, que está sumando a la x, en lugar de restarlo; el coeficiente de x es 1.
- Pista del LLM: Revisa con calma el paso que escribiste, comparándolo con la ecuación anterior. Fíjate bien en cada parte del cambio que hiciste. Tú puedes encontrarlo, ¡sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-061 (ampliado)
- Ejercicio: Resuelve: 4x + 7 = 2x + 19
- Paso anterior: `4x - 2x + 7 = 19`
- Paso del estudiante: `4x - 2x = 18 - 7`
- Lo que realmente pasó: Error de transcripción: al copiar el paso anterior escribe 18 en lugar de 19.
- Pista del LLM: Revisa con calma este paso comparándolo con el anterior. Fíjate bien en cada número y en cada signo de ambas líneas, y no tengas prisa. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): signo
- Marca (a/b/c/d): c

## AMP-062 (ampliado)
- Ejercicio: Resuelve: 5x + 3 - x = 2x + 11
- Paso anterior: `5x + 3 - x = 2x + 11`
- Paso del estudiante: `5x - 2x = 11 - 3`
- Lo que realmente pasó: Omite el término -x al reescribir la ecuación; simplemente lo olvida.
- Pista del LLM: Revisa con calma este paso y compara cada término del paso anterior con los que aparecen ahora. Fíjate bien en los signos y en si todos los términos de cada lado se han tomado en cuenta. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): signo
- Marca (a/b/c/d): b

## AMP-063 (ampliado)
- Ejercicio: Resuelve: 6x - 5 = 2x + 7
- Paso anterior: `6x - 5 - 2x = 7`
- Paso del estudiante: `6x - 2 = 7 + 5`
- Lo que realmente pasó: Al reescribir el paso pierde la x del término -2x y lo convierte en la constante -2.
- Pista del LLM: Revisa con calma el paso que escribiste al final, en especial cómo pasaste los términos de un lado del signo igual al otro. Mira cada número y cada signo con atención antes de seguir, y comprueba si lo que hiciste en ese paso se mantiene igual en ambos lados. Tómate tu tiempo: tú puedes encontrarlo.
- Causas que nombra (automático): signo, un_lado
- Marca (a/b/c/d): a

## AMP-064 (ampliado)
- Ejercicio: Resuelve: (x + 5)/5 + 2 = 5
- Paso anterior: `(x + 5)/5 = 3`
- Paso del estudiante: `x = 3`
- Lo que realmente pasó: Cancela mal la fracción: tacha el 5 que suma en el numerador con el 5 del denominador.
- Pista del LLM: Revisa con calma el paso que hiciste para llegar a x = 3. Vuelve a mirar cada operación que aplicaste, una por una, y comprueba si el resultado sigue manteniendo la igualdad. Tú puedes encontrarlo, ¡sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-065 (ampliado)
- Ejercicio: Resuelve: x/2 + 3 = 7
- Paso anterior: `x/2 + 3 = 7`
- Paso del estudiante: `x/5 = 7`
- Lo que realmente pasó: Error de orden de operaciones: lee x/2 + 3 como x/(2 + 3) y suma el 3 al denominador.
- Pista del LLM: No te preocupes, equivocarse es parte de aprender. Tómate un momento para revisar este paso con calma, fijándote en cada término y en cada operación que hiciste al pasar de la ecuación anterior. Vuelve a comprobarlo con atención.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-066 (ampliado)
- Ejercicio: Resuelve: (2/3)x - 1 = 5
- Paso anterior: `(2/3)x = 5 + 1`
- Paso del estudiante: `(3/2)x = 6`
- Lo que realmente pasó: Al copiar el término invierte la fracción del coeficiente y escribe 3/2 en lugar de 2/3.
- Pista del LLM: Compara con cuidado el paso que escribiste con el anterior, revisando cada número y cada signo. Verifica si lo que hiciste en cada lado de la igualdad mantiene el equilibrio. Tómate tu tiempo, vas por buen camino.
- Causas que nombra (automático): signo
- Marca (a/b/c/d): c

## AMP-067 (ampliado)
- Ejercicio: Resuelve: 2.9x + 1 = 6.8
- Paso anterior: `2.9x = 5.8`
- Paso del estudiante: `3x = 5.8`
- Lo que realmente pasó: Redondea el coeficiente 2.9 a 3 para facilitar la división, cambiando la ecuación.
- Pista del LLM: Revisa con calma cómo pasaste del paso anterior a este. Compara cada número y cada operación con lo que había antes, y comprueba que el cambio sea el que corresponde.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-068 (ampliado)
- Ejercicio: Resuelve: x - 4 * 2 = 10
- Paso anterior: `x - 4 * 2 = 10`
- Paso del estudiante: `2x - 8 = 10`
- Lo que realmente pasó: Error de orden de operaciones: interpreta x - 4 * 2 como (x - 4) * 2 y multiplica también la x.
- Pista del LLM: Revisa con calma cómo pasaste de la ecuación anterior a este nuevo paso. Fíjate en cada operación que hiciste, una por una, y compara lo que había con lo que quedó. ¡Tú puedes encontrar el detalle, sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-069 (ampliado)
- Ejercicio: Resuelve: 7x - 3 = 4x + 5 + 4
- Paso anterior: `7x - 3 = 4x + 9`
- Paso del estudiante: `7x - 4x - 4x = 9 + 3`
- Lo que realmente pasó: Escribe dos veces el término -4x al pasarlo al lado izquierdo, duplicándolo.
- Pista del LLM: Revisa con calma cómo pasaste cada término de un lado al otro del signo igual. Fíjate en el signo de cada número y en lo que le hiciste a la x del lado derecho. Tómate tu tiempo: si revisas paso a paso, seguro encuentras dónde está el detalle.
- Causas que nombra (automático): signo
- Marca (a/b/c/d): b

## AMP-070 (ampliado)
- Ejercicio: Resuelve: 5x - 13 = 22
- Paso anterior: `5x - 13 = 22`
- Paso del estudiante: `x + 5 - 13 = 22`
- Lo que realmente pasó: Interpreta 5x como x + 5, confundiendo la multiplicación implícita con una suma.
- Pista del LLM: Revisa con calma el segundo paso que escribiste y compáralo con el primero. Fíjate bien en qué parte de la expresión cambió y si ese cambio respeta lo que dice la ecuación original. Tómate tu tiempo, tú puedes encontrarlo.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-072 (ampliado)
- Ejercicio: Resuelve: 7x - 4 = 3x + 5 + 3
- Paso anterior: `7x - 4 = 3x + 8`
- Paso del estudiante: `5x = 8 - 4`
- Lo que realmente pasó: Combina simplificacion_aritmetica (calcula 7x - 3x como 5x) y error_signo (pasa el -4 sin cambiarle el signo).
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior, parte por parte.
Fíjate bien en cada operación que hiciste antes de seguir.
¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-073 (ampliado)
- Ejercicio: Resuelve: x/4 - 2 = 5
- Paso anterior: `x/4 - 2 = 5`
- Paso del estudiante: `x - 2 = 24`
- Lo que realmente pasó: Combina operacion_un_lado (multiplica por 4 pero deja el -2 sin multiplicar) y simplificacion_aritmetica (calcula 5 * 4 = 24).
- Pista del LLM: Vas por buen camino. Revisa con calma el paso que hiciste desde la ecuación anterior. Fíjate bien en cada término y en ambos lados de la igualdad, y comprueba si todo cambió de la misma manera.
- Causas que nombra (automático): un_lado
- Marca (a/b/c/d): c

## AMP-074 (ampliado)
- Ejercicio: Resuelve: 5x - 2(x + 4) = 10
- Paso anterior: `5x - 2(x + 4) = 10`
- Paso del estudiante: `4x + 8 = 10`
- Lo que realmente pasó: Combina distributiva_incorrecta (escribe -2 * 4 como +8) y simplificacion_aritmetica (calcula 5x - 2x como 4x).
- Pista del LLM: Revisa con calma cómo pasaste de la ecuación anterior a este nuevo paso. Fíjate bien en cada parte de la expresión y compara, una por una, las operaciones que hiciste con lo que hay escrito arriba. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-075 (ampliado)
- Ejercicio: Resuelve: 5x + 6 = 2x + 21
- Paso anterior: `3x + 6 = 21`
- Paso del estudiante: `x = (21 + 6)/2`
- Lo que realmente pasó: Combina error_signo (pasa el +6 sin cambiarle el signo) y division_coeficiente_equivocado (divide entre 2 en vez de 3).
- Pista del LLM: Vas bien encaminado, pero este paso tiene algo que conviene revisar. Tómate tu tiempo, compara con calma esta expresión con la anterior y revisa cada parte de tu cálculo. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): aritmetica
- Marca (a/b/c/d): a

## AMP-076 (ampliado)
- Ejercicio: Resuelve: x/3 - 4 = 7 - 5
- Paso anterior: `x/3 - 4 = 2`
- Paso del estudiante: `x = 2 - 4`
- Lo que realmente pasó: Combina operacion_un_lado (quita el denominador 3 sin multiplicar el otro lado) y error_signo (pasa el -4 sin cambiarle el signo).
- Pista del LLM: Revisa con calma cómo pasaste de la ecuación anterior a este nuevo paso. Observa cada operación y cada término con atención, porque puede que haya más de un detalle por corregir. ¡Tú puedes lograrlo, sigue intentándolo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-077 (ampliado)
- Ejercicio: Resuelve: 2(x + 1)/3 = 4
- Paso anterior: `2(x + 1)/3 = 4`
- Paso del estudiante: `2x + 1 = 4`
- Lo que realmente pasó: Combina operacion_un_lado (elimina el denominador 3 sin multiplicar el 4) y distributiva_incorrecta (no multiplica el 1 por 2).
- Pista del LLM: Revisa con calma el paso que escribiste después de la ecuación original. Compara cada término de un lado con el otro y fíjate si todo lo que estaba dentro del paréntesis y debajo de la fracción se trató de la misma forma. Tómate tu tiempo, tú puedes encontrarlo.
- Causas que nombra (automático): distributiva
- Marca (a/b/c/d): b

## AMP-078 (ampliado)
- Ejercicio: Resuelve: 4x - 3 = 2x + 9
- Paso anterior: `2x = 9 + 3`
- Paso del estudiante: `x = 13/3`
- Lo que realmente pasó: Combina simplificacion_aritmetica (suma 9 + 3 = 13) y division_coeficiente_equivocado (divide entre 3 en vez de 2).
- Pista del LLM: Revisa este paso con calma y fíjate bien en cada operación que hiciste para llegar a él. Tómate tu tiempo para comprobarlo línea por línea. ¡Tú puedes encontrar el detalle, sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-079 (ampliado)
- Ejercicio: Resuelve: 5x - 10 = 20
- Paso anterior: `5x = 20 + 10`
- Paso del estudiante: `x = 20/4 + 10`
- Lo que realmente pasó: Combina operacion_un_lado (divide solo el 20 y no el 10) y division_coeficiente_equivocado (divide entre 4 en vez de 5).
- Pista del LLM: ¡Buen intento! Revisa este paso con calma y compara lo que tenías antes con lo que escribiste ahora. Fíjate bien en cada número y en cada operación de la nueva línea.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-097 (ampliado)
- Ejercicio: Resuelve: x/2 + 1 = 3/4
- Paso anterior: `x/2 + 1 = 3/4`
- Paso del estudiante: `4x + 1 = 6`
- Lo que realmente pasó: Aplica multiplicación en cruz entre x/2 y 3/4 aunque el lado izquierdo tiene además el término +1, que copia sin cambios.
- Pista del LLM: Este paso merece una segunda mirada. Revísalo con calma, parte por parte, fijándote en cada término y en cada operación que aplicaste. Tómate tu tiempo, seguro lo encuentras.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-098 (ampliado)
- Ejercicio: Resuelve: x + 2x - 4 = 11
- Paso anterior: `x + 2x - 4 = 11`
- Paso del estudiante: `1 + 2x - 4 = 11`
- Lo que realmente pasó: Reemplaza la x sola por el número 1, confundiendo coeficiente 1 con valor 1.
- Pista del LLM: Revisa con calma lo que cambiaste en la parte izquierda de la ecuación al pasar del paso anterior a este. Compara cada término con el original, uno por uno, y fíjate si todo quedó como debía. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-099 (ampliado)
- Ejercicio: Resuelve: x/4 + 2 = 5
- Paso anterior: `x/4 = 3`
- Paso del estudiante: `x - 4 = 3`
- Lo que realmente pasó: Interpreta la raya de fracción x/4 como una resta y escribe x - 4.
- Pista del LLM: Revisa con calma el paso que escribiste después de x/4 = 3. Compara lo que cambió entre una línea y otra y fíjate si cada operación se aplicó a toda la expresión de forma correcta. Tómate tu tiempo, ¡tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP-100 (ampliado)
- Ejercicio: Resuelve: 3 + x/2 = 5
- Paso anterior: `3 + x/2 = 5`
- Paso del estudiante: `3 + x = 10`
- Lo que realmente pasó: Error de orden de operaciones: lee 3 + x/2 como (3 + x)/2 y multiplica todo por 2 sin multiplicar el 3.
- Pista del LLM: Compara tu último paso con el anterior, con calma. Fíjate bien en cada término de la ecuación y en lo que le pasó a cada uno al realizar la operación. ¡Tú puedes encontrar el error!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-020 (ampliado_2)
- Ejercicio: Resuelve: 2x/3 - 1 = 7
- Paso anterior: `2x/3 = 8`
- Paso del estudiante: `x = 8/2`
- Lo que realmente pasó: Coeficiente fraccionario 2/3: divide solo para 2 e ignora el denominador 3. [Etiqueta cambiada por la autora el 28/10/2026, de division_coeficiente_equivocado a indeterminado: con un coeficiente fraccionario se deja indeterminado, igual que AMP-020 y los casos de dev.]
- Pista del LLM: Revisa con calma el paso que escribiste al pasar de la ecuación anterior a la nueva. Vuelve a mirar cada parte de la operación y fíjate si todo quedó como debía. Tómate tu tiempo, porque a veces un detalle pequeño cambia todo el resultado.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-021 (ampliado_2)
- Ejercicio: Resuelve: 4(x - 3) = 2x + 6
- Paso anterior: `4(x - 3) = 2x + 6`
- Paso del estudiante: `4x - 3 + 2x = 6`
- Lo que realmente pasó: Dos errores en el mismo paso: no multiplica el 4 por el -3 (distributiva) y pasa el 2x a la izquierda sin cambiarle el signo (signo).
- Pista del LLM: Revisa con calma cómo pasaste de la expresión anterior a este paso. Compara lo que escribiste con lo que tenías antes y fíjate si cada parte quedó bien escrita. Tómate tu tiempo y vuelve a trabajarlo paso a paso.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-022 (ampliado_2)
- Ejercicio: Resuelve: 6x - 5 = 2x + 11
- Paso anterior: `6x - 5 = 2x + 11`
- Paso del estudiante: `8x = 17`
- Lo que realmente pasó: Dos errores en un paso: suma 2x en vez de restarlo (signo) y además calcula 11 + 5 como 17 (aritmética).
- Pista del LLM: Revisa con calma este paso, comparándolo con la ecuación anterior término por término. Fíjate bien en los signos y en cada número que escribiste, porque puede que se te haya escapado algo. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): signo
- Marca (a/b/c/d): c

## AMP2-024 (ampliado_2)
- Ejercicio: Resuelve: 2 + 3(x - 1) = 17
- Paso anterior: `2 + 3(x - 1) = 17`
- Paso del estudiante: `5(x - 1) = 17`
- Lo que realmente pasó: Error de orden de operaciones: suma 2 + 3 antes de multiplicar el 3 por el paréntesis.
- Pista del LLM: Revisa con calma cómo cambió cada parte de la expresión al pasar al paso siguiente. Mira con atención qué operación hiciste y sobre qué términos la aplicaste. Tú puedes encontrar el error, ¡sigue intentando!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-025 (ampliado_2)
- Ejercicio: Resuelve: (x + 1)/2 + x/3 = 4
- Paso anterior: `(x + 1)/2 + x/3 = 4`
- Paso del estudiante: `2(x + 1) + 3x = 24`
- Lo que realmente pasó: Error al quitar denominadores: multiplica cada numerador por su propio denominador en lugar de por 6 entre ese denominador.
- Pista del LLM: Revisa con calma cómo pasaste de la ecuación anterior a esta. Compara cada término, uno por uno, y verifica si cada cambio es correcto. ¡Tú puedes encontrar el detalle!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-046 (ampliado_2)
- Ejercicio: Resuelve: 0.3x + 2 = 0.8
- Paso anterior: `0.3x + 2 = 0.8`
- Paso del estudiante: `3x + 2 = 80`
- Lo que realmente pasó: Dos errores en un paso: no multiplica el 2 por 10 y calcula 0.8 por 10 como 80.
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior, lado por lado. Fíjate bien en cada número de ambos lados de la igualdad. Tú puedes encontrar qué está pasando.
- Causas que nombra (automático): un_lado
- Marca (a/b/c/d): c

## AMP2-047 (ampliado_2)
- Ejercicio: Resuelve: -4(x - 2) = 2x + 20
- Paso anterior: `-4x + 8 = 2x + 20`
- Paso del estudiante: `-4x + 2x = 20`
- Lo que realmente pasó: Dos errores en un paso: pasa el 2x sin cambiar signo y quita el 8 del lado izquierdo sin compensarlo en el derecho.
- Pista del LLM: Revisa con calma cada cambio que hiciste en este paso y compara cómo quedó cada lado de la igualdad. Tómate tu tiempo, tú puedes encontrar qué conviene revisar.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-048 (ampliado_2)
- Ejercicio: Resuelve: 4x - 8 = 12
- Paso anterior: `4x - 8 = 12`
- Paso del estudiante: `4(x - 8) = 12`
- Lo que realmente pasó: Error de factor común: saca el 4 pero deja el 8 sin dividir.
- Pista del LLM: Revisa con calma el paso que escribiste frente al anterior. Fíjate bien en cada término de la expresión y en cómo cambia al pasar al nuevo paso. Compara las dos ecuaciones y comprueba que cada transformación sea correcta.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-049 (ampliado_2)
- Ejercicio: Resuelve: (x + 3)/4 = 2
- Paso anterior: `(x + 3)/4 = 2`
- Paso del estudiante: `x + 3 = 2/4`
- Lo que realmente pasó: Error al quitar el denominador: lo pasa dividiendo en lugar de multiplicando.
- Pista del LLM: ¡Buen intento! Compara con calma tu paso con el anterior y revisa cada parte de la operación que hiciste. Fíjate en cómo queda cada lado de la igualdad después del cambio.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-050 (ampliado_2)
- Ejercicio: Resuelve: 6 + 4x/2 = 14
- Paso anterior: `6 + 4x/2 = 14`
- Paso del estudiante: `(6 + 4x)/2 = 14`
- Lo que realmente pasó: Error de orden de operaciones: interpreta 6 + 4x/2 como si todo estuviera dividido para 2.
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior, fijándote en cada detalle de la expresión. Algo no coincide del todo, así que tómate tu tiempo para encontrarlo. ¡Tú puedes!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-072 (ampliado_2)
- Ejercicio: Resuelve: 5 - 3(x + 2) = x
- Paso anterior: `5 - 3(x + 2) = x`
- Paso del estudiante: `5 - 3x + 6 + x = 0`
- Lo que realmente pasó: Dos errores en un paso: -3 por 2 lo escribe como +6 (distributiva) y pasa la x a la izquierda como +x (signo).
- Pista del LLM: Buen esfuerzo, vas por buen camino. Revisa con calma este paso, comparándolo con el paso anterior. Tómate tu tiempo para verificar que cada parte quedó bien escrita.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-073 (ampliado_2)
- Ejercicio: Resuelve: 3x - 2 = x + 10
- Paso anterior: `3x - x = 10 + 2`
- Paso del estudiante: `x = 13/3`
- Lo que realmente pasó: Dos errores en un paso: calcula 10 + 2 como 13 (aritmética) y divide para 3 en lugar de 2 (coeficiente equivocado).
- Pista del LLM: Revisa con calma el paso que acabas de escribir y compáralo con el anterior. Tómate tu tiempo para verificar cada cálculo que hiciste hasta llegar a ese resultado. No te desanimes, con paciencia lo lograrás.
- Causas que nombra (automático): aritmetica
- Marca (a/b/c/d): b

## AMP2-074 (ampliado_2)
- Ejercicio: Resuelve: (2x - 1)/5 = 3/2
- Paso anterior: `(2x - 1)/5 = 3/2`
- Paso del estudiante: `5(2x - 1) = 6`
- Lo que realmente pasó: Error al multiplicar en cruz: multiplica cada numerador por su propio denominador.
- Pista del LLM: Revisa con calma cómo pasaste de la ecuación anterior a esta nueva. Verifica que cada operación se haya aplicado de manera completa y correcta sobre todos los términos. ¡Tómate tu tiempo, tú puedes corregirlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-075 (ampliado_2)
- Ejercicio: Resuelve: 3x + 4 = 25
- Paso anterior: `3x + 4 = 25`
- Paso del estudiante: `7x = 25`
- Lo que realmente pasó: Error de términos semejantes: suma 3x + 4 como 7x.
- Pista del LLM: Revisa con calma cómo pasaste de la primera ecuación a la segunda. Mira cada término que cambió y comprueba que cada cambio se haya hecho con cuidado. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-090 (ampliado_2)
- Ejercicio: Resuelve: 6x - 2(x + 3) = 2x + 4
- Paso anterior: `4x - 6 = 2x + 4`
- Paso del estudiante: `2x = 11`
- Lo que realmente pasó: Paréntesis y x en ambos lados: al agrupar calcula 4 + 6 como 11.
- Pista del LLM: Revisa este paso con calma, comparando cada término con la ecuación anterior. Verifica cada cuenta que hiciste, una por una. Tómate tu tiempo, puedes lograrlo.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): e

## AMP2-095 (ampliado_2)
- Ejercicio: Resuelve: x/5 - 2 = 1
- Paso anterior: `x/5 = 3`
- Paso del estudiante: `x = 3/5`
- Lo que realmente pasó: Coeficiente 1/5: divide para 5 en lugar de 1/5 (equivale a multiplicar por 5). [Etiqueta cambiada por la autora el 28/10/2026, de division_coeficiente_equivocado a indeterminado: con un coeficiente fraccionario se deja indeterminado, igual que AMP-020 y los casos de dev.]
- Pista del LLM: Revisa con calma el paso que acabas de escribir y compáralo con el anterior. Fíjate bien en cada número y en cómo cambió la expresión. Tómate tu tiempo, vas por buen camino y sé que puedes encontrarlo.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-096 (ampliado_2)
- Ejercicio: Resuelve: 2 + x/4 = 1/4
- Paso anterior: `2 + x/4 = 1/4`
- Paso del estudiante: `x/4 = 3/4`
- Lo que realmente pasó: Dos errores en un paso: el 2 pasa sumando en vez de restando (signo) y suma 1/4 + 2 como 3/4 (aritmética con fracciones).
- Pista del LLM: Vuelve a revisar con calma el paso que escribiste. Observa con atención cada lado de la igualdad y compáralo con el paso anterior. Tómate tu tiempo, equivocarse también es parte de aprender.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-097 (ampliado_2)
- Ejercicio: Resuelve: 2(3x - 5) = 14
- Paso anterior: `2(3x - 5) = 14`
- Paso del estudiante: `6x = 18`
- Lo que realmente pasó: Dos errores en un paso: no multiplica el 2 por el -5 (distributiva) y además calcula 14 + 5 como 18 (aritmética).
- Pista del LLM: Revisa con calma este paso y compara cada término con el paso anterior. Verifica que cada operación se haya hecho completa y con cuidado. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## AMP2-098 (ampliado_2)
- Ejercicio: Resuelve: 12 - 4 * 2 + x = 9
- Paso anterior: `12 - 4 * 2 + x = 9`
- Paso del estudiante: `8 * 2 + x = 9`
- Lo que realmente pasó: Error de orden de operaciones: resta 12 - 4 antes de multiplicar 4 * 2.
- Pista del LLM: Revisa con calma este paso y compara cada parte con el paso anterior, una por una. Tómate tu tiempo para encontrar dónde puede estar la diferencia. ¡Vas por buen camino!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-010 (prueba_ciega)
- Ejercicio: Resuelve: x/4 - 3 = 2
- Paso anterior: `x/4 = 5`
- Paso del estudiante: `4 * x/4 = 5`
- Lo que realmente pasó: Multiplica por 4 solo el lado de la x para quitar el denominador.
- Pista del LLM: Revisa con calma el paso que escribiste después del anterior. Compara lo que tienes ahora con lo que había antes y fíjate bien en cada cambio que hiciste. Tómate tu tiempo: a veces un detalle pequeño hace toda la diferencia. ¡Tú puedes lograrlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-015 (prueba_ciega)
- Ejercicio: Resuelve: 3x + 14 = 65
- Paso anterior: `3x = 51`
- Paso del estudiante: `x = 16`
- Lo que realmente pasó: Divide entre 3 correctamente, pero calcula 51 / 3 = 16.
- Pista del LLM: Revisa con calma el paso que hiciste desde 3x = 51 hasta x = 16. Vuelve a comprobar cada cuenta de ese paso y observa si el resultado concuerda con la ecuación original. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): e

## PC-021 (prueba_ciega)
- Ejercicio: Resuelve: 2(x + 4) = x - 3
- Paso anterior: `2(x + 4) = x - 3`
- Paso del estudiante: `2x + 4 + x = -3`
- Lo que realmente pasó: Dos errores en un paso: no multiplica el 2 por el 4 (distributiva) y pasa la x a la izquierda sin cambiarle el signo.
- Pista del LLM: Este paso todavía no está bien. Compáralo con calma con la ecuación anterior, parte por parte, y revisa qué cambió en cada lado del signo igual. Tú puedes encontrar lo que falta corregir.
- Causas que nombra (automático): signo
- Marca (a/b/c/d): c

## PC-022 (prueba_ciega)
- Ejercicio: Resuelve: 0.2x + 1.5 = 3.9
- Paso anterior: `0.2x + 1.5 = 3.9`
- Paso del estudiante: `0.2x = 5.2`
- Lo que realmente pasó: Dos errores en un paso: suma el 1.5 en lugar de restarlo (signo) y además calcula 3.9 + 1.5 = 5.2 en lugar de 5.4.
- Pista del LLM: Revisa con calma cómo pasaste de la línea anterior a esta. Compara los dos renglones paso a paso y fíjate bien en cada número y en cada operación que hiciste. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-023 (prueba_ciega)
- Ejercicio: Resuelve: 5(2x - 3) = 4x + 15
- Paso anterior: `5(2x - 3) = 4x + 15`
- Paso del estudiante: `7x - 3 = 4x + 15`
- Lo que realmente pasó: Dos errores en un paso: suma 5 + 2 en lugar de multiplicar (5 * 2x = 10x) y no multiplica el 5 por el -3.
- Pista del LLM: Revisa con calma el paso que hiciste al pasar de la línea anterior a la nueva. Fíjate bien en cada término y en cómo se transforma al operar, y compáralo parte por parte con lo que había antes. Tómate tu tiempo, seguro lo encuentras.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-024 (prueba_ciega)
- Ejercicio: Resuelve: 7 + 2x = 25
- Paso anterior: `7 + 2x = 25`
- Paso del estudiante: `9x = 25`
- Lo que realmente pasó: Reduce términos no semejantes: suma el 7 con el 2x como si ambos tuvieran x.
- Pista del LLM: Revisa con calma el paso que hiciste al pasar de la primera ecuación a la segunda. Fíjate bien en cada término y en cómo quedó cada parte de la expresión. Tómate tu tiempo y vuelve a intentarlo, ¡tú puedes!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-025 (prueba_ciega)
- Ejercicio: Resuelve: x/2 + 1 = (x + 5)/3
- Paso anterior: `x/2 + 1 = (x + 5)/3`
- Paso del estudiante: `3x + 1 = 2(x + 5)`
- Lo que realmente pasó: Error al quitar denominadores: multiplica por 6 las fracciones pero no el término entero 1.
- Pista del LLM: Revisa con calma este paso y compara cada término con la ecuación anterior. Fíjate bien en cómo quedó cada parte después de la transformación. Tú puedes encontrar el error, ¡sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-035 (prueba_ciega)
- Ejercicio: Resuelve: 2x/5 = 4
- Paso anterior: `2x/5 = 4`
- Paso del estudiante: `5 * 2x/5 = 4`
- Lo que realmente pasó: Multiplica por 5 solo el lado izquierdo.
- Pista del LLM: Revisa con calma este paso comparándolo con el anterior. Fíjate bien en qué cambió y en qué se mantuvo igual en cada lado de la igualdad. ¡Tú puedes encontrarlo, vas por buen camino!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-041 (prueba_ciega)
- Ejercicio: Resuelve: 2x/3 - 1 = x/2 + 3
- Paso anterior: `6 * 2x/3 - 6 * 1 = 6 * x/2 + 6 * 3`
- Paso del estudiante: `4x - 6 = 3x + 9`
- Lo que realmente pasó: Con fracciones en ambos lados, multiplica todo por 6, pero calcula 6 * 3 = 9.
- Pista del LLM: Hay un detalle en este paso que conviene revisar. Compara cada término con el paso anterior, operación por operación, y tómate tu tiempo para encontrarlo.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-042 (prueba_ciega)
- Ejercicio: Resuelve: 6x + 5 = 2
- Paso anterior: `6x = -3`
- Paso del estudiante: `x = 6/(-3)`
- Lo que realmente pasó: Invierte la división: divide 6 entre -3 en lugar de dividir -3 entre el coeficiente 6.
- Pista del LLM: Tómate un momento para revisar con calma el paso en el que pasaste de 6x = -3 a x = 6/(-3). Verifica cada parte de ese paso antes de continuar. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-046 (prueba_ciega)
- Ejercicio: Resuelve: -3(x - 4) = 2x - 3
- Paso anterior: `-3(x - 4) = 2x - 3`
- Paso del estudiante: `-3x - 12 + 2x = -3`
- Lo que realmente pasó: Dos errores en un paso: escribe -12 en lugar de +12 al distribuir y pasa el 2x sin cambiarle el signo.
- Pista del LLM: Revisa este paso con calma, término por término, y compáralo con el paso anterior. Tómate tu tiempo: cada línea debe seguir de forma exacta lo que venía antes. Si lo revisas con cuidado, seguro encontrarás lo que hay que corregir.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-047 (prueba_ciega)
- Ejercicio: Resuelve: 5x - 9 = 2x + 12
- Paso anterior: `5x - 9 = 2x + 12`
- Paso del estudiante: `5x + 2x = 12`
- Lo que realmente pasó: Dos errores en un paso: pasa el 2x sin cambiarle el signo y elimina el -9 de la izquierda sin compensarlo en la derecha.
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con la línea anterior. Fíjate con atención en cada término de la nueva expresión, sin apurarte. Equivocarse es parte de aprender, ¡tú puedes corregirlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-048 (prueba_ciega)
- Ejercicio: Resuelve: 4x + 8 = 20
- Paso anterior: `4x + 8 = 20`
- Paso del estudiante: `4(x + 8) = 20`
- Lo que realmente pasó: Error de factor común: saca el 4 pero no divide el 8 entre 4.
- Pista del LLM: Revisa con calma el paso que escribiste, comparándolo con el anterior. Piensa si ambas expresiones realmente representan lo mismo. Tómate tu tiempo, seguro encontrarás qué revisar.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-049 (prueba_ciega)
- Ejercicio: Resuelve: 5x + 4 = 29
- Paso anterior: `5x = 25`
- Paso del estudiante: `x = 25 - 5`
- Lo que realmente pasó: Usa la operación inversa equivocada: resta el coeficiente en lugar de dividir entre él.
- Pista del LLM: Revisa con calma el paso que escribiste: cada cambio que hiciste al pasar de una línea a la siguiente debe mantener la igualdad. Mira con atención la operación que usaste y comprueba si el resultado es el que corresponde. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-050 (prueba_ciega)
- Ejercicio: Resuelve: 20 - 2(x + 3) = 4
- Paso anterior: `20 - 2(x + 3) = 4`
- Paso del estudiante: `18(x + 3) = 4`
- Lo que realmente pasó: Error de orden de operaciones: resta 20 - 2 antes de aplicar la multiplicación por el paréntesis.
- Pista del LLM: Revisa con calma este paso y compáralo con el anterior, término por término. Asegúrate de que cada parte de la expresión se haya transformado correctamente. Tú puedes encontrar el detalle que hay que corregir, ¡sigue adelante!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-062 (prueba_ciega)
- Ejercicio: Resuelve: (3x + 6)/4 = x
- Paso anterior: `(3x + 6)/4 = x`
- Paso del estudiante: `4 * (3x + 6)/4 = x`
- Lo que realmente pasó: Con fracción y x en ambos lados, multiplica por 4 solo el lado izquierdo.
- Pista del LLM: Revisa este paso con calma, comparándolo con el anterior. Fíjate bien en cada parte de la ecuación y en cómo cambió. Seguro que lo encuentras, ¡tú puedes!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-073 (prueba_ciega)
- Ejercicio: Resuelve: 5(x + 2) = 30
- Paso anterior: `5(x + 2) = 30`
- Paso del estudiante: `5x = 30 + 2`
- Lo que realmente pasó: Dos errores en un paso: no multiplica el 5 por el 2 y pasa ese término al otro lado sin cambiarle el signo.
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior. Fíjate bien en cada parte de la expresión y en cómo cambia de un paso a otro. Tómate tu tiempo, puedes lograrlo.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-093 (prueba_ciega)
- Ejercicio: Resuelve: 3x/4 + 1 = 7
- Paso anterior: `3x/4 = 6`
- Paso del estudiante: `x = 6/3`
- Lo que realmente pasó: Divide entre 3 ignorando el denominador; el coeficiente de x es 3/4.
- Pista del LLM: Vas por buen camino al intentar despejar la x, pero este paso merece una segunda mirada. Revisa con calma qué le ocurrió a cada término de la igualdad y compara cómo quedó tu expresión con la anterior. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c

## PC-097 (prueba_ciega)
- Ejercicio: Resuelve: x/2 - 7 = 15
- Paso anterior: `x/2 - 7 = 15`
- Paso del estudiante: `x/2 = 9`
- Lo que realmente pasó: Dos errores en un paso: resta el 7 en lugar de sumarlo y además calcula 15 - 7 = 9.
- Pista del LLM: Revisa con calma el cambio que hiciste en este paso, comparándolo con el paso anterior. Fíjate bien en cada número y vuelve a hacer los cálculos con cuidado. ¡Tú puedes encontrarlo!
- Causas que nombra (automático): aritmetica
- Marca (a/b/c/d): b

## PC-099 (prueba_ciega)
- Ejercicio: Resuelve: 4x + 2 * 3 = 18
- Paso anterior: `4x + 2 * 3 = 18`
- Paso del estudiante: `12x + 6 = 18`
- Lo que realmente pasó: Error de orden de operaciones: trata 4x + 2 como si estuviera entre paréntesis y multiplica todo por 3.
- Pista del LLM: Revisa con calma el paso que escribiste y compáralo con el anterior, parte por parte. Fíjate bien en cada cambio que hiciste y en cada número que aparece. Vas por buen camino, tómate el tiempo para verificarlo.
- Causas que nombra (automático): ninguna
- Marca (a/b/c/d): c
