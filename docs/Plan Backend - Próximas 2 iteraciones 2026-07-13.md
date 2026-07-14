# Plan de Desarrollo Backend — Próximas 2 iteraciones

**Fecha:** 2026-07-13
**Alcance:** 2 iteraciones / 4 semanas · Enfoque híbrido (estabilización + feature)
**Dedicación estimada:** ~33% jornada → **~3–4 días ideales por iteración** (≈7–8 días ideales en total)
**Base de partida:** backend en commit `1864a29`, Alembic head `b557707b768a` (en sync con `dev.db`)

---

## 1. Objetivos del plan

1. **Cerrar lo que está a medias:** cablear el motor de Bessel (ya programado, pero inaccesible por API) y arreglar los bugs conocidos del flujo de importación.
2. **Endurecer lo existente:** unificar autenticación, evitar datos huérfanos, sentar bases de test.
3. **Avanzar el roadmap:** importación masiva de coordenadas de referencia (Iter 5) y motor de coordenadas aproximadas (Iter 6).

> **Principio de priorización:** las tareas marcadas como **[Core]** forman el camino mínimo para cerrar cada iteración. Las **[Opcional]** entran si sobra capacidad dentro del ~33%.

---

## 2. Estado de partida (resumen)

| Iter roadmap | Estado | Comentario |
|---|---|---|
| 1 · Proyectos | ✅ | CRUD + parámetros geodésicos/CRS |
| 2 · Sesiones + auth | ⚠️ | CRUD y auth OK, pero **4 routers sin auth** y borrado en cascada incompleto |
| 3 · Parser GKA | ✅ | Funciona; con bugs de hash/cascada (ver A2) |
| 4 · Bessel | ⚠️ | Motor matemático hecho (`BesselAdjuster`), **no cableado a endpoint** |
| 5 · Coords. referencia | ⚠️ | Solo CRUD; **sin importación masiva** |
| 6 · Coords. aproximadas | ❌ | Solo scaffolding CRUD; **sin motor de cálculo** |
| 7–14 | ❌ | No iniciadas |

**Stack:** Python 3.14, FastAPI, SQLAlchemy 2.0, Alembic, SQLite (`dev.db`), pandas, gps-time, pyproj, JWT, bcrypt. **Sin `pytest`, sin SciPy, sin Docker/CI.**

---

## 3. Iteración A — Estabilización y cierre de Bessel (semanas 1–2)

**Entregable:** backend seguro y consistente en el flujo importación → Bessel, con tests automáticos cubriendo el camino crítico.

### A1 · Unificar autenticación en todos los routers  · [Core] · S (0.5 d)

**Descripción.** Los routers de `raw-observation`, `bessel`, `reference` y `approximate` no exigen `CurrentUser`; cualquiera puede leer/escribir datos sin token. Hay que alinearlos con `project`, `import-session`, `station-setup` y `user`, que ya lo exigen.

**Criterios de aceptación**
- Todos los endpoints bajo `/api/v1` (salvo `auth/login` y `auth/register`) requieren JWT válido.
- Petición sin token → `401`. Token inválido/expirado → `401`.
- Los endpoints existentes siguen funcionando con token válido.

**Archivos afectados**
- `api/routes/raw_observation_router.py`
- `api/routes/bessel_observation_router.py`
- `api/routes/reference_coordinate_router.py`
- `api/routes/approximate_coordinate_router.py`
- Patrón a replicar: `api/routes/station_setup_router.py` (parámetro `_: CurrentUser`).

**Dependencias:** ninguna.
**Notas:** considerar extraer un `Depends` o middleware si se prefiere a nivel de app en vez de por-endpoint (decisión de estilo).

---

### A2 · Arreglar bugs del flujo de importación GKA  · [Core] · M (1–1.5 d)

**Descripción.** Tres defectos detectados al reproducir la importación real:

1. **`content_hash` es `unique=True` global** (`data/database/models/import_session.py:15`), pero el chequeo de la app es **por proyecto** (`get_by_project_and_hash`). Importar el mismo fichero en un proyecto distinto pasa el chequeo y luego revienta con `IntegrityError` → **500 sin capturar**.
2. **`delete_import_session` borra los `station_setups` pero no sus `raw_observations`** (`services/import_session_service.py:84-98`) → observaciones huérfanas. `delete_station_setup` tiene el mismo problema.
3. **Mensaje de duplicado poco accionable:** "Este archivo ya ha sido importado" no indica en qué proyecto/sesión está.

**Decisión pendiente (bloquea el diseño):** *¿un mismo fichero GKA debe poder importarse en varios proyectos?* → **Recomendación: SÍ** (proyectos distintos = obras/presas distintas). Eso implica eliminar el `unique` global y dejar unicidad por `(project_id, content_hash)`.

**Criterios de aceptación**
- El mismo fichero se puede importar en **distintos proyectos** sin error; reimportarlo en el **mismo** proyecto sigue dando 400 con mensaje claro (incluye `project_id`/sesión previa).
- Borrar una sesión de importación elimina en cascada sus `station_setups` **y** sus `raw_observations` (sin filas huérfanas). Lo mismo al borrar un `station_setup`.
- El `IntegrityError` residual, si quedase, se captura y devuelve 400 (no 500).

**Archivos afectados**
- `data/database/models/import_session.py` (quitar `unique=True`, opcional composite unique)
- `data/database/models/station_setup.py` y `raw_observation.py` (considerar `ondelete="CASCADE"` en los FK + activar `PRAGMA foreign_keys=ON` en SQLite, o mantener borrado manual)
- Nueva migración Alembic
- `services/import_session_service.py`, `services/station_setup_service.py` (borrado en cascada)
- `services/import_orchestrator_service.py` (mensaje de error)

**Dependencias:** ninguna.
**Notas:** activar `PRAGMA foreign_keys=ON` en `data/database/engine.py` (`connect_args`/event listener) simplifica las cascadas, pero cambia el comportamiento del dev.db actual — evaluar.

---

### A3 · Cablear el motor de Bessel a un endpoint  · [Core] · M (1.5 d)

**Descripción.** `BesselAdjuster.adjust_bessel()` ya hace la reducción (promedio círculo directo/inverso, ángulos/distance Bessel y deltas), pero **solo se invoca en `tests/bessel_tests.py`**. Falta: un endpoint que dispare el cálculo para un estacionamiento, persista las `BesselObservation` y permita recalcular.

**Criterios de aceptación**
- `POST /api/v1/station-setups/{station_setup_id}/bessel` (o equivalente) calcula y **persiste** las observaciones Bessel para ese estacionamiento.
- Es **idempotente**: recalcular sustituye las filas previas de ese `station_setup` (borra + reescribe, o upsert).
- Si no hay pares directo/inverso válidos → `400`/`422` con mensaje claro ("No hay observaciones válidas con observaciones directas e inversas").
- Devuelve la lista de `BesselObservationResponse` creada.
- (Opcional) Variante a nivel de sesión: `POST /api/v1/import-sessions/{id}/bessel` que itera todos sus estacionamientos.

**Archivos afectados**
- `services/bessel_observation_service.py` → nuevo método `calculate_for_station_setup(id)` (o un `BesselCalculationService` en `services/calculations/`)
- `api/routes/bessel_observation_router.py` o `station_setup_router.py` → nuevo endpoint
- `api/dependencies.py` → cablear dependencias (repositorio de raw observations para alimentar el adjuster)
- Reutiliza `services/calculations/bessel_adjuster.py` sin cambios de fondo

**Dependencias:** A1 (el nuevo endpoint debe llevar auth).
**Notas:** el `BesselAdjuster` ya filtra `v_angle != 0` y `distance != 0`; confirmar que ese criterio es el deseado para datos reales (descarta visuales cenitales/colimación).

---

### A4 · Infraestructura de tests (pytest) + tests del camino crítico  · [Core] · M (1.5 d)

**Descripción.** No hay `pytest`; los "tests" son scripts manuales (`if __name__ == "__main__"`). Hay que meter test real sobre lo que más duele: parser, importación (deduplicación), Bessel y auth.

**Criterios de aceptación**
- `pytest` (+ `httpx` para `TestClient`) añadido a `pyproject.toml`.
- `tests/conftest.py` con una **DB SQLite temporal** (en memoria o fichero efímero) y fixtures de cliente/cliente autenticado.
- Tests verde cubriendo:
  - Parser GKA sobre `docs/*.gka` ( nº de estacionamientos y observaciones, circle ∈ {1,2}).
  - Orquestador: importación OK + **deduplicación por proyecto** (tras A2).
  - `BesselAdjuster`: corrección numérica frente a valores conocidos (caso sintético directo+inverso).
  - Auth: endpoint protegido sin token → 401; con token → 200.

**Archivos afectados**
- `pyproject.toml` (deps + configuración pytest)
- `tests/conftest.py` (nuevo)
- `tests/test_gka_parser.py`, `tests/test_import_orchestrator.py`, `tests/test_bessel_adjuster.py`, `tests/test_auth.py` (nuevos)

**Dependencias:** A2 (dedup) y A3 (endpoint Bessel) para poder testear su comportamiento final.

---

## 4. Iteración B — Coordenadas de referencia y motor de aproximadas (semanas 3–4)

**Entregable:** importación masiva de bases de referencia y motor de coordenadas aproximadas operativos por API; datos filtrables por proyecto.

### B1 · Importación masiva de coordenadas de referencia  · [Core] · M (1.5 d)

**Descripción.** Iter 5. Hoy solo existe CRUD manual de `ReferenceCoordinate`. Falta un endpoint de subida de fichero que cree muchas filas asociadas a un proyecto.

**Decisión pendiente (bloquea):** *¿formato del fichero?* → **Recomendación: CSV** (`target_name,x,y,z` con cabecera) por simplicidad; valorar también un formato topográfico concreto si la obra lo provee.

**Criterios de aceptación**
- `POST /api/v1/projects/{project_id}/reference-coordinates/import` acepta un fichero y crea las `ReferenceCoordinate` vinculadas al proyecto.
- Manejo de duplicados por `target_name` dentro del proyecto: actualizar (upsert) o saltar con warning — decisión a confirmar.
- Errores por línea (formato, no numérico) se reportan sin abortar toda la carga; se devuelve resumen (creadas / actualizadas / fallidas + detalle).
- Requiere auth (coherente con A1).

**Archivos afectados**
- `api/routes/reference_coordinate_router.py` (endpoint `UploadFile`)
- Nuevo parser/`ReferenceCoordinateImportService` (p.ej. `services/parsers/csv_reference_parser.py`)
- `api/dependencies.py`, `services/reference_coordinate_service.py`

**Dependencias:** A1.
**Notas:** seguir el patrón del `import_gka` (validar extensión, `decode("utf-8")`, transacción controlada).

---

### B2 · Motor de cálculo de coordenadas aproximadas  · [Core] · L/XL (2–3 d)

**Descripción.** Iter 6. Hoy `ApproximateCoordinate` es solo CRUD (vinculado a `bessel_observation_id`). Falta el **motor matemático** que, a partir de un estacionamiento con coordenadas conocidas (referencia) + observaciones Bessel, calcule coordenadas aproximadas de los puntos nuevos, y aporte los **cierre angular y en distancia** y detección de errores groseros.

**Criterios de aceptación**
- `services/calculations/approximate_coordinate_calculator.py` que, dado un `station_setup` (con `etr_x/y/z` orientados) + sus `BesselObservation` + `ReferenceCoordinate`, calcule y persista `ApproximateCoordinate` por objetivo.
- Endpoint `POST /api/v1/station-setups/{id}/approximate-coordinates` (y/o a nivel de sesión) que dispare el cálculo.
- Devuelve, además de las coordenadas, **indicadores semafóricos**: cierre angular y en distancia dentro de tolerancia (definida en el proyecto/parámetros) → marca ok/fuera de tolerancia.
- Requiere que el estacionamiento tenga coordenadas ETR y orientación (`desorientacion`); si no → error claro.

**Archivos afectados**
- Nuevo `services/calculations/approximate_coordinate_calculator.py`
- `services/approximate_coordinate_service.py` (método `calculate_for_station_setup`)
- `api/routes/approximate_coordinate_router.py` o `station_setup_router.py` (endpoint)
- `api/dependencies.py`; revisar `data/database/models/station_setup.py` (`etr_*`, `desorientacion`) y `coordinate.py`

**Dependencias:** A3 (necesita `BesselObservation` ya calculadas), B1 (necesita referencias). Posible necesidad de **SciPy/Numpy directo** → añadir a `pyproject.toml` (numpy ya viene con pandas; SciPy solo si la formulación lo requiere).
**Notas:** este es el ítem más grande del plan; si el tiempo aprieta, dejar el endpoint + cálculo polar básico en B2 y diferir la detección de errores groseros a la siguiente iteración.

---

### B3 · Scoping por proyecto / multi-tenancy en endpoints de datos  · [Opcional] · M (1.5 d)

**Descripción.** Hoy `GET /raw-observations`, `/bessel-observations`, etc. devuelven datos **globales** (todo el sistema), sin filtro por proyecto. Para una app multi-proyecto esto es un problema de usabilidad y de aislamiento. Hay que permitir filtrar por `project_id` recorriendo la jerarquía (`raw_observation → station_setup → import_session → project`).

**Criterios de aceptación**
- Los endpoints de listado de datos aceptan `project_id` y devuelven solo lo de ese proyecto.
- (Opcional, si se quiere ahora) asociación usuario↔proyecto + que un usuario solo vea sus proyectos → requiere nueva tabla `project_members`.

**Archivos afectados**
- `data/repositories/*.py` (métodos `get_by_project` con joins), servicios y routers afectados
- (Si se hace permisos) nuevo modelo `project_members`, migración, `api/dependencies.py`

**Dependencias:** ninguna técnica; ideal做完 tras A1.
**Notas:** si los permisos finos no son prioritarios ahora, hacer solo el filtrado por `project_id` (sin modelo de miembros) y dejar permisos para la Fase de autenticación ampliada.

---

## 5. Resumen y estimación

| ID | Tarea | Iter | Tamaño | Días ideales | Prioridad |
|---|---|---|---|---|---|
| A1 | Unificar auth en todos los routers | A | S | 0.5 | Core |
| A2 | Arreglar bugs de importación (hash/cascada) | A | M | 1–1.5 | Core |
| A3 | Cablear motor Bessel a endpoint | A | M | 1.5 | Core |
| A4 | pytest + tests del camino crítico | A | M | 1.5 | Core |
| **A total** | | | | **≈ 4.5–5** | |
| B1 | Import masivo coords. referencia | B | M | 1.5 | Core |
| B2 | Motor coords. aproximadas | B | L/XL | 2–3 | Core |
| B3 | Scoping por proyecto / multi-tenancy | B | M | 1.5 | Opcional |
| **B total** | | | | **≈ 3.5–4.5 (sin B3)** | |

> Con ~3–4 días ideales por iteración al 33%, la **Iteración A** queda justa (A1–A4 son Core); la **Iteración B** encaja B1+B2, y **B3 queda como opcional** si sobra capacidad.

---

## 6. Decisiones pendientes (necesitan tu input antes/durante)

1. **¿Mismo fichero GKA importable en varios proyectos?** (define el diseño de A2 — recomendación: sí).
2. **Formato de importación de coordenadas de referencia** (CSV vs. otro) para B1.
3. **¿Permisos por usuario/proyecto ya (miembros), o solo filtrado `project_id`?** para B3.
4. **¿Activar `PRAGMA foreign_keys=ON`** (cascadas reales en SQLite) o mantener borrado manual en servicio (A2).
5. **¿Meter SciPy como dependencia** de una vez para el motor de ajuste futuro, o esperar a la Iter 7?

---

## 7. Riesgos

- **B2 es grande y depende de A3 + B1.** Si A se retrasa, B2 corre peligro → mitigación: dejar el cálculo polar básico antes que la detección de errores groseros.
- **Criterio de validez del `BesselAdjuster`** (`v_angle != 0`, `distance != 0`) puede descartar visuales legítimas en datasets reales → validar con los `.gka` de `docs/`.
- **Multi-tenancy (B3)** tocada a destiempo puede generar retrabajo en repositorios; conviene decidir el patrón de `get_by_project` cuanto antes aunque se ejecute después.

---

## 8. Entregable global de las 2 iteraciones

- Flujo **import → Bessel → persistencia** completo y re-ejecutable por API.
- Importación consistente (sin 500 por hash, sin huérfanos al borrar).
- Auth uniforme en toda la API.
- Importación masiva de coordenadas de referencia.
- Motor de coordenadas aproximadas con indicadores de cierre.
- Suite de tests automática sobre el camino crítico.
- (Si llega) datos filtrables por proyecto.
