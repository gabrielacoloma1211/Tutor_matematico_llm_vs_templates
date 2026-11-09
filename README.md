# Tutor Matemático — Retroalimentación con LLM frente a plantillas contextualizadas

Prototipo del proyecto integrador (USFQ): *"Evaluación Comparativa de la Generación de Retroalimentación
Pedagógica con LLM frente a Plantillas Contextualizadas en un Tutor con Verificación Simbólica de Errores
Algebraicos para Noveno de EGB"*.

## Cómo funciona

```
paso del estudiante (S_i → S_i+1)
        │
        ▼
Verificador simbólico (SymPy, determinista)
   ├── paso válido ──▶ confirmación al estudiante
   └── paso inválido ──▶ Módulo de diagnóstico (árbol de decisión, determinista)
                                   │  categoría de error
                                   ▼
                         Generador de retroalimentación
                            ├── LLM (arquitectura propuesta)
                            └── plantilla contextualizada (versión de referencia)
```

El verificador y el diagnóstico son los mismos en las dos configuraciones que se comparan; lo único que cambia
es cómo se genera la pista pedagógica.

## Estructura del proyecto

```
├── src/
│   ├── verificador/      # Componente 1: verificación simbólica determinista (SymPy)
│   ├── diagnostico/      # Componente 2: clasificación del error (árbol de decisión, determinista)
│   ├── generador/        # Componente 3: generación de retroalimentación
│   │   ├── llm.py            # arquitectura propuesta (usa un LLM)
│   │   └── plantillas.py     # versión de referencia (plantillas contextualizadas, sin LLM)
│   └── api/              # Backend FastAPI que expone el sistema
├── tests/                # Pruebas (verificador, entrada, API, diagnóstico, benchmark y prueba ciega)
│   └── datos/            # ejemplos de las pruebas en JSON (no están escritos dentro del código)
├── benchmark/
│   ├── casos/dev/        # 100 casos de desarrollo (para diseñar y probar las reglas)
│   ├── casos/test/       # 50 casos de evaluación final (no se usan para diseñar reglas)
│   ├── casos/ampliado/   # 100 casos adicionales generados por un LLM, conjunto aparte (ver más abajo)
│   ├── casos/variaciones/# 2 lotes de 50 variaciones de AMP-010 y AMP-071 (otros números)
│   ├── casos/ampliado_2/   # primera prueba ciega, ya usada para ajustar (75 de ajuste, 25 reservados)
│   ├── casos/prueba_ciega/ # nueva prueba ciega: 100 casos solo para medir (no se ajusta nada con ellos)
│   ├── casos/evaluacion_docente/ # 30 casos para los docentes y 20 del piloto (seleccionados al azar con semilla fija)
│   ├── validar_casos.py  # comprueba la consistencia matemática de los casos (enunciado, pasos, despeje)
├── evaluacion/
│   ├── comun.py                # lo que comparten los scripts: predecir, métricas, resumen, guardado con fecha
│   ├── evaluar_diagnostico.py  # exactitud y macro-F1 sobre dev (o test, una sola vez)
│   ├── evaluar_ampliado.py     # lo mismo sobre el conjunto ampliado, separado en ajuste y reservados
│   ├── evaluar_variaciones.py  # el diagnóstico sobre las variaciones
│   ├── evaluar_prueba_ciega.py # mide el diagnóstico sobre la prueba ciega (guarda huellas del código y los casos)
│   ├── medir_latencia.py       # latencia del verificador y del diagnóstico (dev)
│   ├── piloto_modelos.py       # compara modelos de LLM sobre los 20 casos del piloto (lectura ciega)
│   ├── probar_llm_en_indeterminado.py # llama al LLM en los casos indeterminados para ver si inventa una causa
│   ├── generar_pistas_docentes.py # genera las pistas de los 30 casos (LLM y plantillas), las asigna A/B y arma la hoja
│   ├── docentes/               # hoja para los docentes (PLANTILLA_DOCENTES.md) y sus pistas, clave A/B y hoja final
│   └── resultados/             # resultados guardados con fecha, una carpeta por tema:
│       ├── ampliado/  ampliado_2/  variaciones/  prueba_ciega/   # el diagnóstico sobre cada conjunto
│       ├── latencia/                                             # latencia del verificador y del diagnóstico
│       ├── piloto_llm/                                           # piloto para elegir el modelo de LLM
│       └── indeterminado_con_llm/                                # qué hace el LLM cuando el diagnóstico es indeterminado
└── data/
    ├── taxonomia.json    # Las 6 categorías de error (5 + indeterminado)
    ├── plantillas.json   # Los textos de las pistas con plantillas y los avisos de la API (no están en el código)
    ├── prompt_llm.txt    # El prompt del LLM (no está en el código)
    └── prompt_llm_indeterminado.txt # El prompt de la prueba del LLM en casos indeterminados
```

## Estado actual

| Componente | Estado |
|---|---|
| Verificador simbólico | Implementado y probado (casos válidos, inválidos y errores de parseo). La discrepancia conserva las expresiones de cada lado sin expandir y también el texto de las ecuaciones tal como se escribieron (SymPy simplifica y pierde, por ejemplo, el paréntesis de `3x + (x - 7)` o el `- 7` de `2x + 7 - 7`). |
| Benchmark | 150 casos (100 dev + 50 test), elaborados y etiquetados por la autora y validados con el verificador. Además, dos conjuntos ampliados de 100 casos cada uno (generados por un LLM y etiquetados por la autora; el segundo fue la primera prueba ciega), 100 variaciones y una nueva prueba ciega de 100 casos solo para medir (ver abajo). El validador comprueba también que el enunciado coincida con la ecuación inicial y que el último paso sea el despeje (`x = valor`) y satisfaga esa ecuación. |
| Módulo de diagnóstico | Implementado: árbol de decisión de 6 categorías (distributiva, un solo lado, aritmética, división, signo, indeterminado) más detectores de errores que la taxonomía no tiene como categoría (orden de operaciones, factor común mal sacado, cada lado por su propio denominador), que se informan como `indeterminado` con su explicación. Sobre los casos dev: 100/100. |
| Evaluación del diagnóstico | Dev 100/100. El conjunto test (50) está reservado para una única evaluación final. Primera prueba ciega: 83/100, macro-F1 0.83 (medición sin ajustes), luego ajustada y usada como ampliado 2 (96/100 con etiquetas corregidas, optimista). Nueva prueba ciega: 89/100, macro-F1 0.90. Conjuntos ampliados y variaciones: ver las secciones de abajo. |
| Generador con plantillas | Implementado (`src/generador/plantillas.py`): rellena `{termino}`, `{factor}` y `{coeficiente}` con los detalles del diagnóstico, usa una segunda plantilla para el signo perdido al multiplicar y responde con un mensaje general si el diagnóstico es `indeterminado` o falta un dato. Sin LLM, determinista. |
| Generador con LLM | Implementado (`src/generador/llm.py`) con el SDK de Anthropic, cliente inyectable y registro de latencia y tokens. Modelo elegido con un piloto de 20 casos (`claude-haiku-5-5`; ver "Experimentos con llamadas reales al LLM"). Las pruebas automáticas usan un cliente falso; las llamadas reales se hicieron en los pilotos y en la prueba con casos indeterminados, y sus resultados quedan guardados con su configuración. |
| API | `/salud`, `/verificar` (verificador → diagnóstico → pista con `modo` plantilla o llm) e interfaz web en `/`; una ecuación mal escrita responde HTTP 422 (error de formato), no `valido=false`; el LLM no disponible responde 503. Toda entrada pasa por `src/verificador/entrada.py` antes de llegar a SymPy (solo expresiones de primer grado, con límites de longitud y complejidad). |

## Instalación

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar las pruebas

```bash
pytest
```

Los tests no usan la clave de la API (el LLM se prueba con un cliente falso). Se ejecutan automáticamente en GitHub Actions (`.github/workflows/tests.yml`) en cada push a `main` y en cada pull request, con Python 3.12 y las dependencias de `requirements.txt`.

## Validar el benchmark

```bash
python benchmark/validar_casos.py                  # casos dev
python benchmark/validar_casos.py benchmark/casos/test
python benchmark/validar_casos.py benchmark/casos/ampliado_2   # (y prueba_ciega cuando esté)
```

## Evaluar el diagnóstico

```bash
python evaluacion/evaluar_diagnostico.py                                  # dev
python evaluacion/evaluar_diagnostico.py --conjunto test --evaluacion-final   # una sola vez, al final
python evaluacion/evaluar_ampliado.py --guardar --etiqueta _ajustado      # conjunto ampliado
python evaluacion/evaluar_variaciones.py variaciones_nuevas.json --guardar
python evaluacion/medir_latencia.py --repeticiones 10 --guardar   # latencia (no usa test)
python evaluacion/evaluar_prueba_ciega.py --medicion-sin-ajuste --guardar   # prueba ciega (solo mide)
```

Cada comando imprime la matriz de confusión, la precisión, el recall y el F1 por categoría y el macro-F1.

Los fallos se cuentan con tres significados distintos, y las tablas los muestran por separado: **abstención** (`indeterminado`: el diagnóstico procesó el caso y decidió no asignar una categoría, algo previsto en el diseño), **`ERROR`** (el diagnóstico lanzó una excepción: es una falla del programa, no una decisión, y cuenta como fallo en el recall y el macro-F1) y **otra categoría** (clasificación equivocada, el fallo más peligroso). Los resultados guardados antes de este cambio llaman "seguros" a las abstenciones y también a los `ERROR`. Solo uno de ellos tuvo un `ERROR`: la corrida del conjunto ampliado del 14 de octubre de 2026 (`resultados/ampliado/ampliado_2026-10-14.txt`, caso AMP-038), que en la tabla de esa fecha se contó como "seguro" y que el código actual ya no produce (la corrida actual del ampliado clasifica AMP-038 sin excepción).

## Ejecutar el servidor de desarrollo

```bash
uvicorn src.api.main:app --reload
```

Luego abre http://127.0.0.1:8000/ para usar la interfaz del estudiante, o http://127.0.0.1:8000/docs para ver la documentación interactiva de la API.

### Interfaz del estudiante

Página web simple en `src/api/static/index.html`, servida por la misma API. El estudiante escribe la ecuación inicial y después su solución paso a paso; cada paso se revisa contra el anterior con `/verificar`. Un selector arriba a la derecha elige quién redacta la pista: una plantilla o el LLM (el verificador y el diagnóstico son los mismos en ambos casos). Un paso incorrecto queda subrayado en rojo con el tipo de error y la pista al lado; no se agrega a la solución y se puede corregir. Los pasos válidos se marcan con una palomita.

### Seguridad y control de uso de la API

La API actual es un **prototipo de investigación para uso local o en un entorno controlado**. No tiene autenticación, ni límite de peticiones por usuario, ni presupuesto de gasto. Lo único que limita las entradas es que cada ecuación tenga como máximo 1000 caracteres.

Esto importa sobre todo en `modo: "llm"`: cada petición que llega al LLM consume tokens de la cuenta de Anthropic de la autora. Si el servicio se publicara en internet tal como está, cualquier persona que conociera la dirección podría generar gasto o saturar el servicio.

Por eso, en esta tesis la API no se publica. Los docentes evalúan hojas impresas (generadas con `evaluacion/generar_pistas_docentes.py`) y no usan el servidor. Si en el futuro el tutor se desplegara para estudiantes reales, antes sería necesario: autenticación (clave por usuario o por institución), límite de peticiones, un tope de gasto en la cuenta del proveedor del LLM y el registro de las peticiones. Estos controles no están implementados y no forman parte del alcance de este trabajo.

### Alcance: ecuaciones con solución x = 0

**Qué hace el verificador.** Comprueba equivalencia: un paso es válido si la ecuación nueva tiene la misma solución que la anterior. No comprueba el procedimiento. Por eso acepta un salto que conserva la solución aunque omita pasos (de `3x + 2 = 8` a `x = 2`), y en principio también aceptaría un paso con dos errores que se compensan. Es un límite general del criterio, no solo del caso x = 0, y se acepta para este prototipo: construir un verificador procedimental está fuera del alcance.

**Por qué se rechaza x = 0.** Con una ecuación sin número suelto (`ax = bx`) todas las ecuaciones de ese tipo tienen la misma solución, x = 0, así que el criterio no puede marcar ningún paso como incorrecto: `(3333x)/2 = 1234x` y `3333x = 1234x` salen como equivalentes aunque el segundo paso es erróneo. En el resto de las ecuaciones, un error casi siempre cambia la solución y se detecta; aquí no, de forma sistemática. Por eso `/verificar` responde HTTP 422 (`entrada_no_permitida`) si la ecuación **anterior** del paso tiene solución x = 0, y la interfaz lo avisa al escribir la ecuación inicial. Un paso nuevo con solución 0 producto de un error (por ejemplo `3x + 2 + 2x = 2`) sí se procesa y se marca incorrecto.

**Costo de la restricción.** Es conservadora: también rechaza pasos correctos de esas ecuaciones (como `2x + 3 = 3` a `2x = 0`). Sobre el benchmark el impacto es nulo: de los 656 casos y las 2334 ecuaciones usadas como paso anterior, ninguna tiene solución 0. Tampoco son ejercicios típicos de noveno de EGB, que se plantean con una solución distinta de cero.

**Alternativa descartada.** Admitir estas ecuaciones y aceptar cualquier paso con solución 0 haría que el sistema diera por buenos pasos erróneos, sin poder avisarlo al estudiante.

La comprobación está en `src/api/main.py` y no en el verificador, para no cambiar el código con el que se midió el diagnóstico. Está cubierta por pruebas en `tests/test_api.py`.

### Controles de la respuesta del LLM

Después de cada llamada, `src/generador/llm.py` revisa la respuesta sin modificarla:
- **Terminó con normalidad.** Si el modelo se detuvo por otro motivo que `end_turn` o `stop_sequence` (por ejemplo, `max_tokens`: la pista quedó cortada), la respuesta no se entrega como pista: la API responde HTTP 503 y la interfaz ofrece la plantilla. Una respuesta vacía se trata igual.
- **Formato.** `revisar_formato()` marca `demasiado_larga` (más de 45 palabras, el límite del prompt), `emojis` y `markdown`. La pista se entrega tal como la escribió el modelo; los incumplimientos se registran en `generacion.incumplimientos` de la respuesta de la API y en los resultados de los scripts (`piloto_modelos.py`, `probar_llm_en_indeterminado.py`).
- **Lo que no se puede comprobar automáticamente.** Si la pista es matemáticamente correcta y pedagógicamente útil la juzgan los docentes. Que no revele la solución se comprueba en los scripts de evaluación, que conocen la corrección esperada de cada caso; la API no la conoce.

### Configuración registrada en cada experimento con el LLM

Para poder repetir un experimento, cada script que llama al LLM (`piloto_modelos.py`, `probar_llm_en_indeterminado.py`) guarda en su JSON de resultados un bloque `configuracion` con: la fecha, el modelo exacto, la temperatura (`null` = no se envía), el máximo de tokens, el tiempo de espera, la huella (SHA-256, 16 primeros caracteres) de cada archivo de prompt usado, el commit y si había cambios sin guardar. La genera `configuracion_experimento()` en `evaluacion/comun.py`. Los resultados guardados antes de este cambio (pilotos del 3 de noviembre y la prueba con indeterminados del 4 de noviembre) no tienen ese bloque.

### Experimentos con llamadas reales al LLM

Hasta ahora se hicieron tres series de llamadas reales a la API de Anthropic. Los resultados están en `evaluacion/resultados/`. El resto de las pruebas automáticas (`pytest`) usa un cliente falso y no llama al servicio.

| Experimento | Fecha | Qué se hizo | Configuración usada | Resultados |
|---|---|---|---|---|
| Piloto 1 y piloto 2 (elección del modelo) | 3 de nov. de 2026 | Dos corridas de `piloto_modelos.py` sobre los 20 casos de `piloto_20.json`, con `claude-sonnet-5-5` y `claude-haiku-5-5`. Lectura ciega de las pistas por la autora. | Temperatura no enviada, **máximo 1024 tokens**, prompt de esa fecha (anterior al cambio del prompt de la auditoría). | `piloto_llm/`. Ninguna pista reveló la solución. Haiku costó unas 10 veces menos que Sonnet (en el piloto 1: 0,0045 USD frente a 0,0514 USD) con latencia media parecida (2,6 a 3,4 s). Se eligió Haiku. En el piloto 2, 1 de las 20 llamadas de Haiku falló. |
| Prueba con casos indeterminados | 4 de nov. de 2026 | `probar_llm_en_indeterminado.py` sobre 90 casos indeterminados (sin los de test), con un prompt propio. | `claude-haiku-5-5`, prompt `prompt_llm_indeterminado.txt`. | `indeterminado_con_llm/`. Descrita en la sección "Pista con LLM". |

Los pilotos y la prueba con indeterminados se hicieron **antes** de tres cambios que están en el código actual: el nuevo prompt de `prompt_llm.txt` (corrección de la auditoría), el máximo de 4096 tokens y las revisiones de formato de la respuesta. Por eso sus JSON no tienen el bloque `configuracion` (ver abajo) y no deben leerse como resultados de la configuración final. La evaluación con los docentes sí se hará con la configuración congelada.

### Pista con LLM

El modo LLM necesita una clave de API de Anthropic en la variable de entorno `ANTHROPIC_API_KEY` (el archivo `.env` ya está en `.gitignore`; no la subas a Git):

```bash
export ANTHROPIC_API_KEY="..."
uvicorn src.api.main:app --reload
```

**Configuración vigente** (la que usará la evaluación con los docentes). Parámetros fijos en `src/generador/llm.py`: modelo (`TUTOR_MODELO_LLM`, por defecto `claude-haiku-5-5`), temperatura **no se envía** (los modelos 5.x la rechazan: se usa el valor por defecto del modelo), máximo 4096 tokens de salida (los modelos 5.x razonan antes de responder y ese razonamiento cuenta; con 200 la respuesta salía vacía o cortada) y 20 s de espera. El prompt está en `data/prompt_llm.txt`. Cada respuesta de `/verificar` incluye `generacion` con la latencia y, con LLM, el modelo y los tokens. Sin clave o si el servicio falla, la API responde HTTP 503 (`llm_no_disponible`) y la interfaz ofrece usar la plantilla. Si el diagnóstico es `indeterminado` no se llama al LLM y se devuelve el mismo mensaje general de la plantilla (`LLAMAR_EN_INDETERMINADO = False`). Se probó llamarlo en los 90 casos indeterminados de dev, ampliado, ampliado 2 y prueba ciega (sin los de test), con un prompt que dice que la causa no se conoce (`data/prompt_llm_indeterminado.txt`, script `evaluacion/probar_llm_en_indeterminado.py`): en 10 de 90 (11%) la pista afirmó una causa no verificada (8 incorrectas o parciales, 2 acertadas), 80 fueron neutras y ninguna reveló la solución. Lectura manual de la autora, una sola corrida y un solo modelo; resultados en `evaluacion/resultados/indeterminado_con_llm/`.

Para **repetir** los experimentos con el LLM (hace falta la clave en `ANTHROPIC_API_KEY` y genera gasto en la cuenta):

```bash
python evaluacion/piloto_modelos.py --guardar                      # piloto de modelos (20 casos)
python evaluacion/probar_llm_en_indeterminado.py --guardar         # LLM en casos indeterminados (90 casos)
python evaluacion/generar_pistas_docentes.py --solo-comprobar      # revisa los 30 casos sin llamar al LLM
python evaluacion/generar_pistas_docentes.py                       # genera las 60 pistas (solo tras el congelado)
```

Cada uno guarda en su JSON el bloque `configuracion` con el modelo, la temperatura, el máximo de tokens y la huella de los prompts realmente usados. Para repetir los pilotos de noviembre con los mismos parámetros, usar `--max-tokens 1024`; el prompt de ese momento no se conserva como archivo aparte (está en el historial de Git). El modelo puede cambiarse con la variable `TUTOR_MODELO_LLM`. Los precios que usa `piloto_modelos.py` para estimar el costo (`PRECIOS`) deben confirmarse en la página oficial de Anthropic antes de citarlos.

`/verificar` recibe `{"s_i": ..., "s_i_mas_1": ..., "modo": "plantilla" | "llm"}` (por defecto `plantilla`) y, si el paso es inválido, devuelve además `pista`, `modo` y `generacion`. Las pruebas automáticas del LLM usan un cliente falso: nunca llaman al servicio real.

## Benchmark

El benchmark es un conjunto de **150 casos** de resolución de ecuaciones de primer grado con una incógnita. Cada caso contiene la resolución correcta paso a paso y una resolución de un estudiante con un error en un paso concreto. Los casos y la categoría de error de cada uno fueron elaborados y asignados por la autora.

### Organización

| Conjunto | Casos | Uso |
|---|---|---|
| `benchmark/casos/dev/` | 100 | Diseñar y probar las reglas del módulo de diagnóstico |
| `benchmark/casos/test/` | 50 | Evaluación final. No se usa para diseñar ni ajustar reglas |

Cada carpeta tiene un archivo `.json` por categoría de la taxonomía (`data/taxonomia.json`). Los dos conjuntos no comparten ecuaciones iniciales.

| Categoría | dev | test |
|---|---|---|
| Error de signo (`error_signo`) | 26 | 13 |
| Propiedad distributiva (`distributiva_incorrecta`) | 20 | 10 |
| Operación en un solo lado (`operacion_un_lado`) | 14 | 7 |
| Simplificación aritmética (`simplificacion_aritmetica`) | 14 | 7 |
| División por coeficiente equivocado (`division_coeficiente_equivocado`) | 14 | 7 |
| Indeterminado (`indeterminado`) | 12 | 6 |
| **Total** | **100** | **50** |

### Formato de un caso

```json
{
  "id": "DEV-001",
  "categoria": "error_signo",
  "enunciado": "Resuelve: 3x - 4 = 13",
  "solucion_correcta": ["3x - 4 = 13", "3x = 13 + 4", "3x = 17", "x = 17/3"],
  "resolucion_estudiante": ["3x - 4 = 13", "3x = 13 - 4", "3x = 9", "x = 3"],
  "indice_paso_erroneo": 1,
  "correccion_esperada": "3x = 13 + 4",
  "pista_referencia": "Revisa el signo del -4 al pasarlo al otro lado.",
  "notas": ""
}
```

- `indice_paso_erroneo`: posición del paso del estudiante que contiene el error. El paso 0 es la ecuación inicial.
- `correccion_esperada`: el paso que debió escribir el estudiante.
- `pista_referencia`: pista pedagógica de referencia para ese error.

### Cómo se elaboraron los casos

- **Un solo error por caso.** Después del error, el estudiante sigue resolviendo normalmente desde su resultado equivocado.
- **Casos indeterminados.** Son pasos que combinan dos errores o que tienen un error que no encaja en ninguna de las otras cinco categorías. En el campo `notas` se explica cómo los clasificaría la autora, por ejemplo `"Combinado = dos errores de signo en un mismo paso."`.
- **Variedad.** Hay ecuaciones con fracciones (65 casos), con paréntesis (76) y con la incógnita en ambos lados (56). El error aparece en el paso 1 en 68 casos y en el paso 2 o posterior en 82.
- **Transiciones.** Los 150 casos suman 1.215 transiciones algebraicas entre pasos consecutivos: 1.065 válidas y 150 inválidas (una por caso). Sobre ellas se evaluará la clasificación de cada transición como válida o inválida, y sobre los 150 pasos erróneos, la clasificación del tipo de error.

## Evaluación con docentes

El instrumento es una comparación **pareada y ciega** sobre los mismos 30 ejercicios (6 por cada una de las 5 categorías de error, elegidos al azar con semilla fija entre los casos con diagnóstico correcto). Cada docente recibe la hoja impresa (`evaluacion/docentes/PLANTILLA_DOCENTES.md`, con una rúbrica de 5 criterios y niveles descritos para el 1, el 3 y el 5) y califica cada pista de forma independiente.

Cómo se genera, con `python evaluacion/generar_pistas_docentes.py` (después del congelado del código):
1. Para cada caso se obtiene el diagnóstico común y se genera una pista con plantillas y otra con el LLM, ambas a partir del mismo paso anterior y del mismo paso del estudiante.
2. Las dos pistas originales se guardan en `evaluacion/docentes/pistas_originales.json`, con la configuración del LLM (modelo, parámetros, huella del prompt, commit). El script no las vuelve a escribir: si el archivo existe solo genera las que falten, y las pistas no se editan a mano.
   Si el proceso se corta y se vuelve a correr, el script reanuda solo lo que falta, pero **antes** compara la configuración actual (modelo, temperatura, máximo de tokens, tiempo de espera, huella de cada prompt, commit y si hay cambios sin guardar) con la registrada al empezar. Si algo cambió (la fecha es lo único que puede variar), se detiene sin llamar al LLM, sin tocar las pistas guardadas y muestra qué cambió. Así las 60 pistas siempre salen de una sola configuración. Si el cambio fue intencional, hay que empezar de nuevo borrando `pistas_originales.json` y `CLAVE_AB_no_entregar.json`.
3. En cada caso se asigna al azar, con semilla fija, cuál es la pista A y cuál la B (15 casos con el LLM como A y 15 con la plantilla). La correspondencia queda aparte, en `CLAVE_AB_no_entregar.json`, y no se entrega a los docentes.
4. Se escribe `HOJAS_DOCENTES_con_pistas.md`: la hoja con las pistas en su lugar, sin decir de qué mecanismo es cada una.
5. Un informe final señala las pistas con incumplimientos de formato o que parecen revelar la solución; no se corrigen ni se reemplazan en silencio.

**Protección del cegamiento.** `pistas_originales.json`, `CLAVE_AB_no_entregar.json`, `HOJAS_DOCENTES_con_pistas.md` y las calificaciones (`calificaciones*`) están en `.gitignore`: no se suben al repositorio público mientras dure la evaluación, porque con ellos se podría saber qué mecanismo escribió cada pista. El script se detiene, antes de escribir nada, si trabaja dentro de un repositorio de Git y esos archivos no están excluidos. A los docentes solo se les entrega la hoja impresa; la clave queda en el computador de la autora. Una vez terminada la evaluación se publicarán las pistas originales, la clave y las calificaciones para que el análisis se pueda reproducir.

Los casos `indeterminado` no entran en esta comparación (el sistema no llama al LLM en ellos). Los resultados de las pruebas ciegas del diagnóstico miden solo la clasificación del error; no permiten concluir que el LLM genere mejores pistas que las plantillas. Esa conclusión depende únicamente de las calificaciones de los docentes.

## Próximos pasos

- [x] Completar las reglas del árbol de decisión en `src/diagnostico/diagnostico.py` y probarlas con los casos dev.
- [x] Agregar pruebas específicas del módulo de diagnóstico (`tests/datos/diagnostico.json`).
- [x] Probar el diagnóstico con un conjunto aparte (ampliado) y con variaciones de los casos que fallan.
- [x] Medir el diagnóstico congelado con una prueba ciega de 100 casos nuevos (83/100). Ajustado después: pasó a ser el ampliado 2.
- [x] Nueva prueba ciega de 100 casos, medida una sola vez (89/100, macro-F1 0.90).
- [x] Implementar `src/generador/plantillas.py` con las plantillas contextualizadas por categoría.
- [x] Implementar `src/generador/llm.py` con la integración a la API del LLM y probarla con la clave real (pilotos).
- [x] Conectar ambos generadores a `/verificar` y crear la interfaz del estudiante.
- [x] Preparar la hoja para los docentes y el script que genera las pistas pareadas y ciegas (`evaluacion/generar_pistas_docentes.py`).
- [ ] Congelar el código (commit y tag), generar las 60 pistas una sola vez y entregarlas a los docentes.
- [ ] Evaluación final: exactitud y macro-F1 sobre los casos test (una sola vez), y rúbrica de calidad pedagógica con docentes.