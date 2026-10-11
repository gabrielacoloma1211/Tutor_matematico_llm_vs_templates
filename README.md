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
├── tests/                # Pruebas unitarias (verificador, discrepancia y benchmark)
├── benchmark/
│   ├── casos/dev/        # 100 casos de desarrollo (para diseñar y probar las reglas)
│   ├── casos/test/       # 50 casos de evaluación final (no se usan para diseñar reglas)
│   ├── validar_casos.py  # comprueba la consistencia matemática de los casos
│   └── README.md         # formato de los casos y cómo se elaboraron
└── data/
    └── taxonomia.json    # Las 6 categorías de error (5 + indeterminado)
```

## Estado actual

| Componente | Estado |
|---|---|
| Verificador simbólico | Implementado y probado (casos válidos, inválidos y errores de parseo). La discrepancia conserva también las expresiones originales de cada lado, sin expandir. |
| Benchmark | 150 casos (100 dev + 50 test), elaborados y etiquetados por la autora y validados con el verificador. |
| Módulo de diagnóstico | En desarrollo: tiene la regla de error de signo y la categoría `indeterminado`; faltan las reglas de distributiva, un solo lado, aritmética y división. |
| Generador con plantillas | Esqueleto: falta rellenar las variables de cada plantilla. |
| Generador con LLM | Esqueleto: el prompt está diseñado; falta la integración con la API. |
| API | `/salud` y `/verificar` (verificador → diagnóstico); aún sin generador. |

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
```

## Ejecutar el servidor de desarrollo

```bash
uvicorn src.api.main:app --reload
```

Luego abre http://127.0.0.1:8000/docs para ver la documentación interactiva de la API.

## Próximos pasos

- [ ] Completar las reglas del árbol de decisión en `src/diagnostico/diagnostico.py` y probarlas con los casos dev.
- [ ] Agregar pruebas específicas del módulo de diagnóstico.
- [ ] Implementar `src/generador/plantillas.py` con las plantillas contextualizadas por categoría.
- [ ] Implementar `src/generador/llm.py` con la integración a la API del LLM.
- [ ] Evaluación: exactitud y macro-F1 sobre los casos test, y rúbrica de calidad pedagógica con docentes.

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
