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
│   ├── casos/prueba_ciega/ # 100 casos generados por un LLM solo para medir (no se ajusta nada con ellos)
│   ├── validar_casos.py  # comprueba la consistencia matemática de los casos (enunciado, pasos, despeje)
├── evaluacion/
│   ├── evaluar_diagnostico.py  # exactitud y macro-F1 sobre dev (o test, una sola vez)
│   ├── evaluar_ampliado.py     # lo mismo sobre el conjunto ampliado, separado en ajuste y reservados
│   ├── evaluar_variaciones.py  # el diagnóstico sobre las variaciones
│   ├── evaluar_prueba_ciega.py # mide el diagnóstico sobre la prueba ciega (guarda huellas del código y los casos)
│   ├── medir_latencia.py       # latencia del verificador y del diagnóstico (dev)
│   └── resultados/             # resultados guardados con fecha + notas de los ajustes
└── data/
    └── taxonomia.json    # Las 6 categorías de error (5 + indeterminado)
```


## Estado actual

| Componente | Estado |
|---|---|
| Verificador simbólico | Implementado y probado (casos válidos, inválidos y errores de parseo). La discrepancia conserva las expresiones de cada lado sin expandir y también el texto de las ecuaciones tal como se escribieron (SymPy simplifica y pierde, por ejemplo, el paréntesis de `3x + (x - 7)` o el `- 7` de `2x + 7 - 7`). |
| Benchmark | 150 casos (100 dev + 50 test), elaborados y etiquetados por la autora y validados con el verificador. Además, un conjunto ampliado de 100 casos generados por un LLM y etiquetados por la autora, 100 variaciones y una prueba ciega de 100 casos generados por un LLM solo para medir (ver abajo). El validador comprueba también que el enunciado coincida con la ecuación inicial y que el último paso sea el despeje (`x = valor`) y satisfaga esa ecuación. |
| Módulo de diagnóstico | Implementado: árbol de decisión de 6 categorías (distributiva, un solo lado, aritmética, división, signo, indeterminado) más detectores de errores que la taxonomía no tiene como categoría (orden de operaciones, factor común mal sacado, cada lado por su propio denominador), que se informan como `indeterminado` con su explicación. Sobre los casos dev: 100/100. |
| Evaluación del diagnóstico | Dev 100/100. El conjunto test (50) está reservado para una única evaluación final. **Prueba ciega: 83/100, macro-F1 0.83** (medición sin ajustes). Conjunto ampliado y variaciones: ver las secciones de abajo. |
| Generador con plantillas | Implementado (`src/generador/plantillas.py`): rellena `{termino}`, `{factor}` y `{coeficiente}` con los detalles del diagnóstico, usa una segunda plantilla para el signo perdido al multiplicar y responde con un mensaje general si el diagnóstico es `indeterminado` o falta un dato. Sin LLM, determinista. |
| Generador con LLM | Implementado (`src/generador/llm.py`) con el SDK de Anthropic, cliente inyectable y registro de latencia y tokens. Probado solo con un cliente falso: falta la primera llamada real y la justificación del modelo. |
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

## Validar el benchmark

```bash
python benchmark/validar_casos.py                  # casos dev
python benchmark/validar_casos.py benchmark/casos/test
python benchmark/validar_casos.py benchmark/casos/prueba_ciega
```

Las variaciones son de un solo paso y no terminan en `x = valor`, por eso solo se validan desde `generar_variaciones.py`, que desactiva la comprobación del despeje (`validar_caso(..., exigir_despeje=False)`).

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

## Ejecutar el servidor de desarrollo

```bash
uvicorn src.api.main:app --reload
```

Luego abre http://127.0.0.1:8000/ para usar la interfaz del estudiante, o http://127.0.0.1:8000/docs para ver la documentación interactiva de la API.

### Interfaz del estudiante

Página web simple en `src/api/static/index.html`, servida por la misma API. El estudiante escribe la ecuación inicial y después su solución paso a paso; cada paso se revisa contra el anterior con `/verificar`. Un selector arriba a la derecha elige quién redacta la pista: una plantilla o el LLM (el verificador y el diagnóstico son los mismos en ambos casos). Un paso incorrecto queda subrayado en rojo con el tipo de error y la pista al lado; no se agrega a la solución y se puede corregir. Los pasos válidos se marcan con una palomita.

### Alcance: ecuaciones con solución x = 0

El criterio de equivalencia (misma solución) no distingue un paso correcto de uno incorrecto cuando la ecuación no tiene un número suelto (`ax = bx`): todas tienen la misma solución, x = 0. Por eso `/verificar` rechaza con HTTP 422 (`entrada_no_permitida`) los pasos cuya ecuación anterior tiene solución x = 0, y la interfaz lo avisa al escribir la ecuación inicial. La comprobación está en `src/api/main.py` y no en el verificador, para no cambiar el código con el que se midió el diagnóstico. Ningún caso de dev ni del ampliado tiene solución 0.

### Pista con LLM

El modo LLM necesita una clave de API de Anthropic en la variable de entorno `ANTHROPIC_API_KEY` (el archivo `.env` ya está en `.gitignore`; no la subas a Git):

```bash
export ANTHROPIC_API_KEY="..."
uvicorn src.api.main:app --reload
```

Parámetros fijos en `src/generador/llm.py`: modelo (`TUTOR_MODELO_LLM`, por defecto `claude-sonnet-5-5`), temperatura 0.2, máximo 200 tokens, 20 s de espera. Cada respuesta de `/verificar` incluye `generacion` con la latencia y, con LLM, el modelo y los tokens. Sin clave o si el servicio falla, la API responde HTTP 503 (`llm_no_disponible`) y la interfaz ofrece usar la plantilla. Si el diagnóstico es `indeterminado` no se llama al LLM y se devuelve el mismo mensaje general de la plantilla (`LLAMAR_EN_INDETERMINADO`).

`/verificar` recibe `{"s_i": ..., "s_i_mas_1": ..., "modo": "plantilla" | "llm"}` (por defecto `plantilla`) y, si el paso es inválido, devuelve además `pista`, `modo` y `generacion`. Las pruebas del LLM usan un cliente falso: nunca llaman al servicio real.

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

## Conjunto ampliado (100 casos generados por un LLM)

Conjunto **aparte** del benchmark (no se mezcla con dev ni test). Un LLM generó 100 variaciones de los casos de la autora, con errores nuevos; la autora las revisó y asignó la categoría oficial. Sirve para ver cómo se comporta el diagnóstico con errores que no vio al diseñar las reglas y para ampliar su repertorio.

| Archivo (`benchmark/casos/ampliado/`) | Contenido |
|---|---|
| `ampliado_original_llm.json` | Los 100 casos tal como los generó el LLM, con la categoría que propuso. |
| `ampliado.json` | Los mismos casos con la categoría oficial de la autora (`categoria`). Conserva la propuesta del LLM (`categoria_propuesta_llm`) y, cuando la autora volvió a revisar un caso, la categoría anterior (`categoria_antes_de_ver_diagnostico`). `tipo_de_novedad`: variante_nueva, estructura_nueva, combinado o fuera_de_taxonomia. |
| `particion.json` | Separa los casos de **ajuste** (74, se usan para modificar reglas) de los **reservados** (26, solo se miden) y marca la muestra de revisión ciega. |

Resultados (`evaluacion/resultados/`):

| Etapa | Exactitud |
|---|---|
| Diagnóstico congelado antes de ajustar (`ampliado_2026-10-14.txt`) | 67/100 |
| Diagnóstico ajustado (`ampliado_2026-10-15_ajustado.txt`) | 99/100 (macro-F1 0.99); ajuste 73/74, reservados 26/26 |

Los fallos se clasifican en *seguros* (responde `indeterminado` o falla sin clasificar) y *peligrosos* (devuelve otra categoría). El caso que sigue mal es AMP-071, una coincidencia numérica (ver variaciones). Como las reglas se ajustaron mirando este conjunto, la cifra del diagnóstico ajustado es optimista: la medición más limpia es la de los casos reservados y la del lote nuevo de variaciones.

El detalle de qué regla se cambió por qué caso está en `evaluacion/resultados/ajustes_tras_conjunto_ampliado.md`. Dev sigue en 100/100 y pasan las 856 pruebas.

## Variaciones de los casos que fallan

La verificación es por equivalencia de solución, así que dos errores en un mismo paso pueden dar por casualidad la misma solución que un error y se leen como si fuera uno. Para comprobar si un caso era coincidencia numérica o una regla faltante, `benchmark/generar_variaciones.py` repite el mismo tipo de error con otros números (semilla fija; descarta las variaciones que resultan válidas por casualidad). Se hicieron 50 variaciones de AMP-010 y AMP-071 (`variaciones.json`, revisadas por la autora) y un lote independiente de otras 50 (`variaciones_nuevas.json`, etiquetas por construcción).

| Etapa | AMP-010 (25) | AMP-071 (25) | Total |
|---|---|---|---|
| Diagnóstico congelado (`variaciones_2026-10-15_congelado.txt`) | 0/25 | 20/25 | 20/50 |
| Con la regla nueva, mismas 50 (no es independiente) | 25/25 | 20/25 | 45/50 |
| Lote nuevo, no usado para diseñar la regla | 25/25 | 23/25 | 48/50 |

AMP-071 era en buena parte coincidencia numérica (con otros números se queda en `indeterminado`). AMP-010 no: faltaba reconocer que el estudiante multiplicó cada lado por su propio denominador, y se agregó esa regla.

## Generador con plantillas

`src/generador/plantillas.py` toma el resultado del diagnóstico y rellena la plantilla de su categoría (`data/taxonomia.json`) con los datos del paso:

| Categoría | Variable | Dato del diagnóstico |
|---|---|---|
| `error_signo` | `{termino}` | `termino` (signo al transponer). Si el signo se perdió al multiplicar toda la ecuación, usa una segunda plantilla con `valor_correcto` y `multiplicador`. |
| `distributiva_incorrecta` | `{factor}` | `factor` |
| `division_coeficiente_equivocado` | `{coeficiente}` | `coeficiente` (se muestra como decimal si el estudiante lo escribió así, `0.5` y no `1/2`) |
| `operacion_un_lado`, `simplificacion_aritmetica` | ninguna | texto fijo |
| `indeterminado` | ninguna | mensaje general; la `explicacion` de los detectores no se usa |

Si falta un dato, devuelve el mensaje general en lugar de dejar una `{variable}` sin reemplazar. Las pruebas (`tests/test_plantillas.py`, 18) cargan sus ejemplos de `tests/datos/plantillas.json`.

## Prueba ciega (100 casos generados por un LLM, solo para medir)

Tercer conjunto aparte, pedido por el tutor. A diferencia del ampliado, **no se ajusta nada con él**: el diagnóstico queda congelado antes de medir y los fallos se informan pero no se usan para cambiar reglas. La categoría la asigna la autora antes de ver la respuesta del diagnóstico.

| Archivo | Contenido |
|---|---|
| `benchmark/casos/prueba_ciega/prueba_ciega.json` | Los 100 casos (16 por categoría, 20 `indeterminado`; 50 variante_nueva, 30 estructura_nueva, 10 combinado, 10 fuera_de_taxonomia). |
| `evaluacion/evaluar_prueba_ciega.py` | Valida los casos, mide el diagnóstico y guarda el resultado con la huella (sha256) del código del verificador, del diagnóstico y de la taxonomía, y la de los casos. Si cambian en una corrida posterior, avisa que la prueba dejó de ser ciega. Exige `--medicion-sin-ajuste`. |
| `tests/test_prueba_ciega.py` | 104 pruebas: casos consistentes, ids únicos, ecuaciones iniciales distintas de las de otros conjuntos y comportamiento del script. |

Resultado (`evaluacion/resultados/prueba_ciega_2026-10-26.txt`, código de huella `6104dd981861a6ce`, casos `b08ec1075f6bacb4`): **83/100, macro-F1 0.83**.

| Categoría | Casos | Precisión | Recall | F1 |
|---|---|---|---|---|
| Error de signo | 16 | 0.84 | 1.00 | 0.91 |
| Distributiva | 16 | 0.81 | 0.81 | 0.81 |
| Operación en un solo lado | 16 | 1.00 | 0.94 | 0.97 |
| Simplificación aritmética | 16 | 0.79 | 0.94 | 0.86 |
| División por coeficiente | 16 | 1.00 | 0.62 | 0.77 |
| Indeterminado | 20 | 0.67 | 0.70 | 0.68 |

De los 17 fallos, 7 fueron seguros (responde `indeterminado`) y 10 peligrosos (otra categoría). Los puntos débiles son la división por coeficiente (5 de sus 16 casos quedaron en `indeterminado`) y `indeterminado`. Con 100 casos, el intervalo de confianza del 95 % de la exactitud va de 0.74 a 0.89. Si se cambia código o etiquetas después de esta medición, deja de ser una prueba ciega y hay que declararlo como ajuste.


## Próximos pasos

- [x] Completar las reglas del árbol de decisión en `src/diagnostico/diagnostico.py` y probarlas con los casos dev.
- [x] Agregar pruebas específicas del módulo de diagnóstico (`tests/datos/diagnostico.json`).
- [x] Probar el diagnóstico con un conjunto aparte (ampliado) y con variaciones de los casos que fallan.
- [x] Medir el diagnóstico congelado con una prueba ciega de 100 casos nuevos (83/100).
- [x] Implementar `src/generador/plantillas.py` con las plantillas contextualizadas por categoría.
- [x] Implementar `src/generador/llm.py` con la integración a la API del LLM (falta probarla con la clave real).
- [x] Conectar ambos generadores a `/verificar` y crear la interfaz del estudiante.
- [ ] Evaluación final: exactitud y macro-F1 sobre los casos test (una sola vez), y rúbrica de calidad pedagógica con docentes.
