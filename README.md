# Tutor Matemático — Verificación Simbólica y Diagnóstico de Errores

Prototipo del proyecto integrador: "Evaluación Comparativa de una Arquitectura de Tutoría con
Verificación Simbólica y Diagnóstico de Errores en Ecuaciones de Primer Grado con una Incógnita
para Noveno de EGB".

## Estructura del proyecto

```
tutor-matematico/
├── src/
│   ├── verificador/      # Componente 1: verificación simbólica determinista (SymPy)
│   ├── diagnostico/      # Componente 2: clasificación del error (árbol de decisión, determinista)
│   ├── generador/        # Componente 3: generación de retroalimentación
│   │   ├── llm.py            # -> arquitectura propuesta (usa LLM)
│   │   └── plantillas.py     # -> versión de referencia (plantillas contextualizadas, sin LLM)
│   └── api/               # Backend FastAPI que expone el sistema
├── tests/                 # Pruebas unitarias
├── benchmark/casos/        # Casos de evaluación anotados (150 casos: 100 dev / 50 test)
└── data/
    └── taxonomia.json      # Las 6 categorías de error (5 + indeterminado)
```

Esta estructura refleja directamente la separación de responsabilidades definida en la
planificación: el verificador determina si un paso es válido y reporta la discrepancia exacta;
el diagnóstico clasifica esa discrepancia según la taxonomía; el LLM (o la plantilla, en la
versión de referencia) solo entra al final, para redactar la retroalimentación.

## Instalación

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar las pruebas

```bash
pytest tests/ -v
```

## Ejecutar el servidor de desarrollo

```bash
uvicorn src.api.main:app --reload
```

Luego abre http://127.0.0.1:8000/docs para ver la documentación interactiva de la API.

## Próximos pasos (semana 2 en adelante)

- [ ] Completar el árbol de decisión en `src/diagnostico/diagnostico.py` para las 5 categorías.
- [ ] Ampliar el verificador para manejar más de una incógnita por nombre (actualmente asume `x`).
- [ ] Implementar `src/generador/llm.py` con la integración a la API de Claude/OpenAI.
- [ ] Implementar `src/generador/plantillas.py` con las plantillas contextualizadas por categoría.
- [ ] Empezar a poblar `benchmark/casos/` con los primeros casos anotados.
