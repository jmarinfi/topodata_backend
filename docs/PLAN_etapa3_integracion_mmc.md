# Plan — Etapa 3: Integración del MMC + persistencia (coords ajustadas como registros)

## Contexto

Las Etapas 1 (calculador puro `LeastSquaresAdjuster`) y 2 (helper `matrix_io`) están listas.
Esta etapa **enciende el MMC** dentro del pipeline de coordenadas aproximadas y **persiste los
resultados**:

- Las 18 matrices → columnas binarias de `StationSetup` (registro crudo del MMC).
- Las **coordenadas ajustadas + precisión** → nuevo modelo **`AdjustedCoordinate`** (registros
  consultables, expuestos por API), en vez de solo blob.

El cálculo se encadena automáticamente al final de
`approximate_coordinate_service.calculate_for_station_setup` (sin endpoint nuevo para dispararlo).

## Decisiones fijadas con el usuario

- **Incógnitas MMC**: solo **puntos de control** (visados que NO son referencia). Las referencias
  son dato conocido (ya fijan la estación vía inversa); se excluyen. Si no hay puntos de control,
  el MMC se omite con `warning` (no rompe el cálculo).
- **`prec_senal`/`prec_punteria`**: se leen de los registros `ApproximateCoordinate` (uno por
  punto) y el cálculo los **preserva** al recrear las coords (hoy el flujo idempotente las resetea
  a los defaults; se arregla).
- **`AdjustedCoordinate(Coordinate)`** (joined-table, `polymorphic_identity="adjusted"`): hereda
  `target_name, x, y, z` (x/y ajustadas; **z se arrastra del approximate**, el MMC es planimétrico)
  y añade `bessel_observation_id, prec_x, prec_y`.
- **18 blobs + registros**: se siguen escribiendo las 18 matrices binarias (registro crudo) **y**
  se crean registros `AdjustedCoordinate` (vista consultable/API). Sin columnas eliminadas.
- **API**: incluir **endpoints GET** de coordenadas ajustadas.

---

## Tareas (pequeñas y específicas)

### Modelo / datos
**T1 — `AdjustedCoordinate`** (`data/database/models/adjusted_coordinate.py`)
```python
class AdjustedCoordinate(Coordinate):
    __tablename__ = "adjusted_coordinates"
    id: Mapped[int] = mapped_column(ForeignKey("coordinates.id"), primary_key=True)
    bessel_observation_id: Mapped[int] = mapped_column(
        ForeignKey("bessel_observations.id"), index=True
    )
    prec_x: Mapped[float] = mapped_column(Float)   # precisión ajustada en x
    prec_y: Mapped[float] = mapped_column(Float)   # precisión ajustada en y
    __mapper_args__ = {"polymorphic_identity": "adjusted"}
```
Registrar en `data/database/models/__init__.py`.

**T2 — Migración Alembic**: crea la tabla `adjusted_coordinates` (joined-table: columna en
`coordinates` + tabla hija con `id` FK, `bessel_observation_id`, `prec_x`, `prec_y`).
`uv run alembic revision --autogenerate -m "modelo AdjustedCoordinate"` → `uv run alembic upgrade head`.

**T3 — `AdjustedCoordinateRepository`** (`data/repositories/adjusted_coordinate_repository.py`):
hereda `BaseRepository[AdjustedCoordinate]` + `get_by_station_setup(id)` y
`delete_by_station_setup(id)` (bulk, borrando también la fila padre `Coordinate`, igual que
`ApproximateCoordinateRepository`). Registrar en `data/repositories/__init__.py`.

### Schemas / DI / API (vertical de lectura)
**T4 — Schemas** (`api/schemas/adjusted_coordinate_schemas.py`): `AdjustedCoordinateBase`
(hereda `CoordinateBase`, añade `bessel_observation_id`, `prec_x`, `prec_y`),
`AdjustedCoordinateCreate`, `AdjustedCoordinateResponse` (`id`, `type="adjusted"`,
`from_attributes=True`). Registrar en `api/schemas/__init__.py`.

**T5 — DI** (`api/dependencies.py`): `get_adjusted_coordinate_repository` +
`AdjustedCoordinateRepositoryDep`; `get_adjusted_coordinate_service` +
`AdjustedCoordinateServiceDep`.

**T6 — `AdjustedCoordinateService`** (`services/adjusted_coordinate_service.py`): solo lectura
(`get_all`, `get_by_station_setup`, `get`, `count`) → `AdjustedCoordinateResponse`. Depende de
`AdjustedCoordinateRepository` + `StationSetupRepository`.

**T7 — Router** (`api/routes/adjusted_coordinate_router.py`): `GET /` , `/by-station-setup/{id}`,
`/{id}`, `/count` (prefijo `/api/v1/adjusted-coordinates`, tag `adjusted-coordinates`, todos con
`_: CurrentUser`). Registrar en `main.py`.

### Integración (núcleo)
**T8 — `ApproximateCoordinateService.calculate_for_station_setup`**:
1. Añadir `repository_adjusted_coordinate: AdjustedCoordinateRepository` al `__init__`.
2. Leer `prec_dist_mm`, `prec_dist_ppm` de `import_session` (junto a `prec_ang_etr`).
3. Tras la **radiación** (línea ~332), antes de persistir:
   - `ref_names = {r.target_name for r in ref_responses}`.
   - **Puntos de control** = `radiaciones` cuyo `target_name` no esté en `ref_names`.
   - Si no hay → `warning`, dejar matrices a `None`, sin registros ajustados.
   - Capturar `prec_by_target = {name: (prec_senal, prec_punteria_cc)}` de los registros
     `ApproximateCoordinate` **existentes** (carga previa, antes del borrado idempotente).
   - Construir `list[LsTarget]` (de los puntos de control) con `approx_x/y, dist_utm,
     acimut` del `RadiacionResult` y `prec_senal/prec_punteria` de `prec_by_target`
     (defaults `0.0`/`3.09` si el punto no tenía registro).
   - Instanciar `LeastSquaresAdjuster(etr_x, etr_y, targets, gon_r, r_cc, s_sexa_cc,
     prec_ang_etr, prec_dist_mm, prec_dist_ppm)` y `calculate()`. **Envolver en
     `try/except ValueError`** → `warnings` (fallo suave, como Bessel).
4. Extender el `update(...)` de `StationSetup` con las **18 matrices** (vía `matrix_io`):
   arrays con `to_bytes` (`v, a, tra_a, p, tra_a_p, x, l, n, inver_n, t, tra_v_p, prec,
   adjust_coord`) y escalares con `scalar_to_bytes` (`desv_post, var_post, num_equations,
   num_unknowns, inter_conf`). Si el MMC falló, estas claves no se añaden (quedan `None`).
5. **Idempotencia ampliada**: `delete_by_station_setup` de coords aproximadas **y** ajustadas.
6. **Recrear** `ApproximateCoordinate` **preservando** `prec_senal/prec_punteria` desde
   `prec_by_target` (pasándolos al `ApproximateCoordinateCreate`).
7. **Crear `AdjustedCoordinate`** (si el MMC fue OK): por cada punto de control único, a partir
   de `result.adjusted_coords` y `result.prec` (`prec_x=prec[2k]`, `prec_y=prec[2k+1]`),
   con `z` arrastrado del `RadiacionResult`.
8. Extender `ApproximateCoordinateCalculationResult` con `desv_post, num_equations,
   num_unknowns, redundancy, adjusted_coordinates: list[AdjustedCoordinateResponse]` (y sumar los
   `warnings` del MMC a los existentes).

> **Orden clave**: el MMC se calcula tras la radiación usando `prec_by_target` capturado de los
> registros previos; **no** requiere que los nuevos registros existan todavía. La recreación de
> coords aproximadas preserva los mismos valores que usó el MMC → coherente entre runs.

### Tests
**T9 — Ampliar `tests/test_approximate_pipeline.py`**: añadir al seed **puntos de control**
(observaciones Bessel con `target_name` no referencia + raw obs). Tras `calculate_for_station_setup`:
- Las 18 columnas `*_matrix` de `StationSetup` no son `None` y `from_bytes` las decodifica con
  shape coherente (p. ej. `a_matrix` cuadrada `2n×2n`).
- Existen registros `AdjustedCoordinate` (uno por punto de control) con `x, y, prec_x, prec_y`.
- Idempotencia: dos runs no duplican ajustadas ni matrices.
- Caso **sin puntos de control** (solo referencias, como el seed actual): el cálculo no falla,
  hay un `warning`, y no hay registros ajustados.

**T10 — `tests/test_adjusted_coordinate.py`**: tras calcular (con puntos de control), los
endpoints `GET /api/v1/adjusted-coordinates/by-station-setup/{id}` y `/{id}` devuelven las
ajustadas (usar `auth_client` + endpoint `POST /station-setups/{id}/approximate-coordinates` para
disparar el cálculo, o llamar al servicio en DB).

### Doc
**T11** — Actualizar `docs/PLAN_ajuste_matricial.md`: marcar MMC integrado + persistencia +
endpoints GET; anotar que `AdjustedCoordinate` sustituye conceptualmente al blob de coords
ajustadas (mantenido por compatibilidad).

---

## Ficheros

**Nuevos:** `data/database/models/adjusted_coordinate.py`,
`data/repositories/adjusted_coordinate_repository.py`,
`api/schemas/adjusted_coordinate_schemas.py`, `services/adjusted_coordinate_service.py`,
`api/routes/adjusted_coordinate_router.py`, `tests/test_adjusted_coordinate.py`, migración Alembic.
**Modificados:** `services/approximate_coordinate_service.py` (integración + extensión del
resultado), `api/dependencies.py`, `main.py`, `data/database/models/__init__.py`,
`data/repositories/__init__.py`, `api/schemas/__init__.py`, `tests/test_approximate_pipeline.py`,
`docs/PLAN_ajuste_matricial.md`.
**Reutiliza:** `LeastSquaresAdjuster`/`LsTarget` (Etapa 1), `matrix_io` (Etapa 2),
`ApproximateCoordinateCalculator.calculate_all_radiaciones`, patrones de
`ApproximateCoordinateRepository`/router.

---

## Verificación (Etapa 3)

1. `uv run alembic upgrade head` — crea `adjusted_coordinates`.
2. `uv run pytest tests/test_approximate_pipeline.py tests/test_adjusted_coordinate.py -v`.
3. `uv run pytest -v` — sin regresiones (Etapas 1-2 incluidas).
4. End-to-end manual: `uv run fastapi dev main.py` → importar `.gka` →
   `POST /api/v1/station-setups/{id}/approximate-coordinates` →
   `GET /api/v1/adjusted-coordinates/by-station-setup/{id}` devuelve coords ajustadas, y la fila
   `station_setups` en `dev.db` tiene las 18 `*_matrix` pobladas.
