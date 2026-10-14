# Tutor Matemático — Retroalimentación con LLM frente a plantillas contextualizadas

Prototipo del proyecto integrador (USFQ): *"Evaluación Comparativa de la Generación de Retroalimentación
Pedagógica con LLM frente a Plantillas Contextualizadas en un Tutor con Verificación Simbólica de Errores
Algebraicos para Noveno de EGB"*.

El sistema revisa, paso a paso, la resolución de ecuaciones de primer grado con una incógnita. Cuando un estudiante
comete un error, identifica de qué tipo es y genera una pista pedagógica. El proyecto compara **dos formas de generar
esa pista**: con un LLM y con plantillas contextualizadas, manteniendo idénticos todo lo demás.

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

`S_i` es el paso anterior y `S_i+1` es el paso que escribe el estudiante. El verificador y el diagnóstico son los
mismos en las dos configuraciones que se comparan; lo único que cambia es el generador de la pista.

## Estado actual

| Componente | Estado |
|---|---|
| Verificador simbólico | Implementado y probado. Cuando un paso es inválido, la discrepancia conserva también las expresiones originales de cada lado, sin expandir. |
| Módulo de diagnóstico | Implementado: árbol de decisión de 6 preguntas, probado con los casos dev. Falta la evaluación final con el conjunto test. |
| Benchmark | 150 casos (100 dev + 50 test), elaborados y etiquetados por la autora y validados con el verificador. |
| Generador con plantillas | Esqueleto: falta rellenar las variables de cada plantilla. |
| Generador con LLM | Esqueleto: el prompt está diseñado; falta la integración con la API. |
| API | `/salud` y `/verificar` (verificador → diagnóstico); aún sin generador. |
| Evaluación con docentes | Pendiente. |

## Cómo ejecutarlo

**Instalación**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Pruebas automáticas**

```bash
pytest
```

**Evaluar el diagnóstico sobre los casos dev** (matriz de confusión, precisión, recall y F1 por categoría)

```bash
python evaluacion/evaluar_diagnostico.py
```

**Validar la consistencia matemática de los casos del benchmark**

```bash
python benchmark/validar_casos.py                  # casos dev
python benchmark/validar_casos.py benchmark/casos/test
```

**Servidor de desarrollo**

```bash
uvicorn src.api.main:app --reload
```

Documentación interactiva en http://127.0.0.1:8000/docs. Ejemplo de uso:

```bash
curl -X POST http://127.0.0.1:8000/verificar \
  -H "Content-Type: application/json" \
  -d '{"s_i": "3(x - 4) = 12", "s_i_mas_1": "3x - 4 = 12"}'
```

```json
{
  "valido": false,
  "categoria_id": "distributiva_incorrecta",
  "categoria_nombre": "Aplicación incorrecta de la propiedad distributiva",
  "discrepancia": {
    "diferencia": "-8",
    "regla": "distributiva_incorrecta",
    "variante": "omite_factor",
    "factor": "3",
    "explicacion": "no multiplicó un término del paréntesis por el factor"
  }
}
```

## Estructura del proyecto

```
├── src/
│   ├── verificador/      # Componente 1: verificación simbólica determinista (SymPy)
│   ├── diagnostico/      # Componente 2: clasificación del error (árbol de decisión, determinista)
│   ├── generador/        # Componente 3: generación de retroalimentación
│   │   ├── llm.py            # arquitectura propuesta (usa un LLM)
│   │   └── plantillas.py     # versión de referencia (plantillas contextualizadas, sin LLM)
│   └── api/              # Backend FastAPI que expone el sistema
├── benchmark/
│   ├── casos/dev/        # 100 casos de desarrollo (para diseñar y probar las reglas)
│   ├── casos/test/       # 50 casos de evaluación final (no se usan para diseñar reglas)
│   ├── casos/ejemplos/   # 6 casos de ejemplo del formato (no forman parte del benchmark)
│   └── validar_casos.py  # comprueba la consistencia matemática de los casos
├── evaluacion/
│   └── evaluar_diagnostico.py   # mide el diagnóstico frente a las categorías asignadas por la autora
├── tests/                # Pruebas automáticas (verificador, discrepancia, diagnóstico y benchmark)
└── data/
    └── taxonomia.json    # Las 6 categorías de error (5 + indeterminado)
```

## Taxonomía de errores

| Categoría | Qué significa | Ejemplo (paso anterior → paso del estudiante) |
|---|---|---|
| `error_signo` | Al mover un término de lado, no le cambia el signo | `6x - 4 = 3` → `6x = 3 - 4` |
| `distributiva_incorrecta` | Al quitar un paréntesis, no multiplica el factor por todos los términos, o lo hace con el signo equivocado | `3(x - 4) = 12` → `3x - 4 = 12` |
| `operacion_un_lado` | Suma, resta, multiplica o divide un valor en un solo lado de la ecuación | `2x + 3 = 11` → `2x = 11` |
| `simplificacion_aritmetica` | Plantea bien la operación, pero se equivoca en el cálculo numérico | `2x = 10 - 3` → `2x = 6` |
| `division_coeficiente_equivocado` | Al despejar, divide entre un número que no es el coeficiente de la incógnita | `5x = 20` → `x = 20/4` |
| `indeterminado` | Dos errores combinados en un paso, o un error que no encaja en ninguna de las anteriores | `2(x + 3) - 4 = 6` → `2x + 3 = 6 - 4` |

## Módulo de diagnóstico

Recibe la discrepancia que reporta el verificador y la clasifica con un árbol de decisión. Las preguntas se hacen en
este orden y la primera que se cumple asigna la categoría:

| # | Pregunta | Categoría |
|---|---|---|
| 1 | ¿Falla en un término distribuido? | `distributiva_incorrecta` |
| 2 | ¿Se operó solo en un lado? | `operacion_un_lado` |
| 3 | ¿Operación bien, cálculo mal? | `simplificacion_aritmetica` |
| 4 | ¿Divisor final incorrecto? | `division_coeficiente_equivocado` |
| 5 | ¿Un término cambió de signo? | `error_signo` |
| 6 | Ninguna aplica con claridad | `indeterminado` |

Las preguntas 1, 2 y 5 se responden generando las versiones erróneas típicas del paso anterior y comprobando si el
paso del estudiante coincide con alguna de ellas. Las preguntas 3 y 4 comparan el paso con el paso correcto. Además de
la categoría, el diagnóstico devuelve una explicación (por ejemplo, el término o el factor involucrado) que luego puede
usar el generador.

## Benchmark

El benchmark es un conjunto de **150 casos** de resolución de ecuaciones de primer grado con una incógnita. Cada caso
contiene la resolución correcta paso a paso y una resolución de un estudiante con un error en un paso concreto. Los
ejercicios provienen de material público; los errores fueron simulados de manera controlada por la autora a partir de
la taxonomía, y la categoría de cada caso fue asignada por la autora.

### Organización

| Conjunto | Casos | Uso |
|---|---|---|
| `benchmark/casos/dev/` | 100 | Diseñar y probar las reglas del módulo de diagnóstico |
| `benchmark/casos/test/` | 50 | Evaluación final. No se usa para diseñar ni ajustar reglas |

Cada carpeta tiene un archivo `.json` por categoría. Los dos conjuntos no comparten ecuaciones iniciales.

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
- **Transiciones.** Los 150 casos suman 1.216 transiciones algebraicas entre pasos consecutivos: 1.066 válidas y 150 inválidas (una por caso).

## Evaluación

Se evalúan dos cosas por separado:

- **El verificador y el diagnóstico**, de forma automática sobre el benchmark:
  - la clasificación de cada transición como válida o inválida, con exactitud (*accuracy*);
  - la clasificación del tipo de error de los 150 pasos erróneos, con *macro-F1* sobre las 6 categorías.
- **La calidad pedagógica de las pistas**, con una rúbrica aplicada de forma ciega por docentes de Matemática.

Con el conjunto dev se diseñan y ajustan las reglas. El conjunto test se usa una sola vez, al final; por eso
`evaluacion/evaluar_diagnostico.py` solo lo ejecuta si se pide explícitamente:

```bash
python evaluacion/evaluar_diagnostico.py --conjunto test --evaluacion-final
```

## Limitaciones conocidas

- **Los errores son simulados.** Los resultados miden el reconocimiento de los patrones de error de la taxonomía, no
  el desempeño frente a errores espontáneos de estudiantes reales, que suelen ser más variados.
- **Las reglas se diseñaron con los casos dev.** Los resultados sobre dev no representan el desempeño del sistema; el
  resultado válido es el del conjunto test.
- **Algunos pasos admiten dos lecturas.** Por ejemplo, ignorar el factor de un paréntesis equivale a dividir solo un
  lado entre ese factor. En esos casos el diagnóstico responde según el orden de las preguntas del árbol.
- **Lo que no reconoce queda como `indeterminado`.** Un error que no corresponde a ninguna variante programada no se
  fuerza a una categoría.

## Próximos pasos

- [ ] Evaluar el diagnóstico sobre el conjunto test.
- [ ] Implementar `src/generador/plantillas.py` con las plantillas contextualizadas por categoría.
- [ ] Implementar `src/generador/llm.py` con la integración a la API del LLM.
- [ ] Evaluar la calidad pedagógica de las pistas con docentes, mediante la rúbrica.
