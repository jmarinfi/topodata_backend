# Plan — Ajuste por mínimos cuadrados (cálculo entre matrices) en TopoData Backend

## Contexto

Los ficheros de `docs/matrices/` especifican un **ajuste por mínimos cuadrados (MMC)** de direcciones + distancias que refina las coordenadas aproximadas radiadas desde un estacionamiento. El flujo es el clásico de ajuste paramétrico:

`A → Aᵀ → P → AᵀP → L → N=AᵀPA → N⁻¹ → t=AᵀPL → x=N⁻¹t → v=Ax−L → vᵀPv → σ̂², σ̂ → precisiones y coords ajustadas`.

El modelo `StationSetup` **ya tiene las 18 columnas `LargeBinary`** para guardar todas estas matrices ([station_setup.py:33-57](../data/database/models/station_setup.py#L33-L57)), añadidas en la migración `142b9835b1b5`, pero **ninguna se lee ni se escribe todavía**. La implementación actual calcula Bessel → posición de estación (resección Cassini + k_utm + Z) → coordenadas aproximadas (desorientación + radiación), pero **no** el ajuste matricial. Este plan cubre esa última etapa y su integración.

**Decisiones ya tomadas con el usuario:**
- **Incógnitas:** todos los puntos visados (uno por observación Bessel) son incógnitas `dx, dy`; la **estación queda fija** en su posición inversa. (Igual que los Excel.)
- **Disparador:** **encadenado automáticamente** al final de `approximate_coordinate_service.calculate_for_station_setup` (sin endpoint nuevo).
- **Precisiones (P):** modelo de precisiones **a priori por observación** confirmado por `docs/matrices/Cálculo parámetros v2.xlsx`. Las componentes son: teodolito (`prec_ang_etr`), error de puntería (`prec_punteria_cc`), error de señal/prisma (`prec_senal`), y distanciómetro (`prec_dist_mm` + `prec_dist_ppm`). Ver fórmulas abajo.

---

## Supuestos a confirmar (importantes)

1. ~~**Fórmula de las precisiones a priori (P).**~~ **CERRADO** — El modelo rico del Excel (`Cálculo parámetros v2.xlsx`) es el correcto. Las 4 componentes de precisión se han añadido al modelo de datos:
   - `prec_dist_mm` y `prec_dist_ppm` en `ImportSession` (distanciómetro, común a toda la sesión).
   - `prec_senal` y `prec_punteria_cc` en `ApproximateCoordinate` (prisma/serial, por punto visado).
   - Ver fórmulas abajo y detalles en `docs/PLAN_etapa1_calculador_mmc.md`.

2. **Redundancia.** Con estación fija y cada punto observado una sola vez, `num_ecuaciones = num_incógnitas = 2N` → **redundancia 0** → el sistema es compatible determinado (`v≈0`, `σ̂²` indefinida). Solo hay redundancia si un punto se observa varias veces o en un ajuste en red. La implementación calculará las matrices igualmente y **gestionará `red≤0`** (σ̂²/σ̂ y precisiones → 0, con `warning`). Los puntos se inician con sus **coordenadas radiadas aproximadas** (las conocidas de referencia no entran en el sistema MMC). Confirmar si se espera otra fuente de redundancia.

3. **`inter_conf` = 1.9599639845400536** (z al 95 %, [Cálculos entre matrices.xlsx!B23](matrices/)). Como no hay endpoint/body (va encadenado), se usa como **constante por defecto** en el calculador y se persiste en `inter_conf_matrix`. Si se quiere editable de verdad, habría que añadir un campo a `ImportSession`/`StationSetup` (fuera de este plan salvo que se pida).

---

## Resumen de las fórmulas (especificación de los Excel)

Por cada punto visado `i` (con coords aproximadas `x_i, y_i`, distancia observada `dist_utm_i`, acimut observado `acim_i = hz_bessel + desorientación`):

- `ΔE = x_i − etr_x`, `ΔN = y_i − etr_y`, `dist_calc = hypot(ΔE, ΔN)`
- `acim_calc = atan2(ΔE, ΔN) / GON_R` (normalizado a [0,400))

**Matriz A** (filas: N direcciones + N distancias; columnas: `dx_P1, dy_P1, …`):
- Fila dirección, columna `dx_i`: `ΔN · R_CC / dist_calc²`  ·  `dy_i`: `−ΔE · R_CC / dist_calc²`
- Fila distancia, columna `dx_i`: `ΔE / dist_utm`  ·  `dy_i`: `ΔN / dist_utm`

**Matriz L** (vector miscierre):
- Dirección: `−(acim_calc − acim_obs) · 10000`
- Distancia: `−(dist_calc − dist_utm)`

**Matriz P** (diagonal). Precisiones a priori por observación (`Cálculo parámetros v2.xlsx` columnas M y N):

```
σ_angular_cc_i = sqrt( (prec_ang_etr · s_sexa_cc)²
                     + (prec_senal_i / dist_utm_i · r_cc)²
                     + prec_punteria_cc_i² )

σ_dist_m_i     = sqrt( prec_senal_i²
                     + (prec_dist_mm/1000 + prec_dist_ppm·1e-6 · dist_utm_i)² )
```

- `prec_ang_etr`, `prec_dist_mm`, `prec_dist_ppm` → `ImportSession` (comunes a toda la sesión).
- `prec_senal_i`, `prec_punteria_cc_i` → `ApproximateCoordinate` (por punto visado).
- Peso dirección `= 1/σ_angular_cc_i²`, peso distancia `= 1/σ_dist_m_i²`.

**Cadena:** `tra_a=Aᵀ`; `tra_a_p=Aᵀ·P`; `n=Aᵀ·P·A`; `inver_n=n⁻¹`; `t=Aᵀ·P·L`; `x=inver_n·t`; `v=A·x−L`; `tra_v_p=vᵀ·P`; `num_eq=filas(A)`; `num_unk=cols(A)`; `red=num_eq−num_unk`; `var_post=(vᵀ·P·v)/red`; `desv_post=√var_post`.

**Salidas:** `prec_i = desv_post · inter_conf · √(inver_n[i,i])`; `coord_ajustada_i = coord_aprox_i + x_i`.

---

## Implementación

### 1. Nuevo calculador puro — `services/calculations/least_squares_adjuster.py`
Sigue el patrón de [station_position_calculator.py](../services/calculations/station_position_calculator.py): **instanciado**, sin tocar DB/repos, toma dataclasses + primitivos, devuelve un `@dataclass`, lanza `ValueError`.

- **Input dataclass** `LsTarget` (desacopla del `RadiacionResult`): `target_name, approx_x, approx_y, dist_utm, acimut_observado, prec_senal, prec_punteria_cc`.
- **Constructor** `(station_x, station_y, targets: list[LsTarget], gon_r, r_cc, s_sexa_cc, prec_ang_etr, prec_dist_mm, prec_dist_ppm, inter_conf=INTER_CONF_DEFAULT)`.
- Método `calculate() -> LeastSquaresResult` que construye A, L, P y ejecuta la cadena con **numpy** (`np.linalg.inv`, `@`). Mapear cada `target_name` → índice de columna; gestionar puntos repetidos (varias observaciones, misma incógnita). Lanzar `ValueError` si `N` es singular, no hay observaciones, o hay distancias nulas. Si `red ≤ 0`: `var_post=desv_post=0`, `prec` a 0, añadir `warning`.
- **`@dataclass LeastSquaresResult`** con todos los arrays numpy (`sigma_dir, sigma_dist, a, tra_a, p, tra_a_p, l, n, inver_n, t, x, v, tra_v_p`), escalares (`num_equations, num_unknowns, redundancy, var_post, desv_post, inter_conf`), `prec` (array 2k) y `adjusted_coords` (lista `(target_name, x, y)`) + `warnings`.
- Constante `INTER_CONF_DEFAULT = 1.9599639845400536`.

### 2. Helper de serialización — `services/calculations/matrix_io.py` **(Etapa 2 completada)**
Implementado en la Etapa 2 (`docs/PLAN_etapa2_matrix_io.md`):
- `to_bytes(arr) -> bytes`: `np.save(io.BytesIO(), np.asarray(arr)).getvalue()` (preserva dtype y shape, sin metadatos externos).
- `from_bytes(b) -> np.ndarray`: `np.load(io.BytesIO(b), allow_pickle=False)` (seguro).
- `scalar_to_bytes(x)` / `scalar_from_bytes(b)` (wrappers para escalares; `.item()`).
- Tests: 10 casos cubriendo round-trip 1D/2D/0-d/empty, dtype int, escalares y keystone con `LeastSquaresResult` real.
- **Pendiente:** representación de `adjust_coord` (lista `(str, float, float)`) → Etapa 3.

### 3. Integración (encadenada) — `services/approximate_coordinate_service.py`
En `calculate_for_station_setup` ([líneas ~319-344](../services/approximate_coordinate_service.py#L319-L344)), **después** de calcular las radiaciones y **antes/tras** persistir los escalares de estación:
- Construir `list[LsTarget]` a partir de los `RadiacionResult` ya en memoria (tienen `target_name, x, y, dist_utm, acimut`) — sin recalcular la radiación.
- Instanciar `LeastSquaresAdjuster(etr_x, etr_y, targets, gon_r, r_cc, s_sexa_cc, prec_ang_etr)` y llamar `calculate()`.
- Serializar los 18 resultados con `matrix_io` y añadirlos al **mismo** `repository_station_setup.update(station_setup, {...})` (extender el dict de [líneas 335-344](../services/approximate_coordinate_service.py#L335-L344)).
- Envolver en `try/except ValueError` y añadir a `warnings` (fallo suave, como Bessel) para no romper el cálculo de coords aproximadas.
- Extender el `@dataclass ApproximateCoordinateCalculationResult` ([líneas 32-46](../services/approximate_coordinate_service.py#L32-L46)) con `desv_post`, `num_equations`, `num_unknowns`, `adjusted_coords`, `precisions` y `ls_warnings` (uso interno/tests).

**Reutilización:** constantes de `Project` (`R_CC`, `S_SEXA_CC`, `GON_R`) en [project.py:24-28](../data/database/models/project.py#L24-L28); `prec_ang_etr` de `ImportSession` ([import_session.py:24-25](../data/database/models/import_session.py#L24-L25)); `RadiacionResult` de [approximate_coordinate_calculator.py](../services/calculations/approximate_coordinate_calculator.py). **No** hace falta nuevo endpoint, nuevo servicio, ni cableado DI nuevo (el `ApproximateCoordinateService` ya tiene todos los repos).

### 4. Modelo de datos (añadido en Etapa 1)
La Etapa 1 (`docs/PLAN_etapa1_calculador_mmc.md`) añadió los 4 campos de precisión a los modelos existentes y generó la migración correspondiente:

- `ImportSession`: `prec_dist_mm` (Float, default=0.8), `prec_dist_ppm` (Float, default=1).
- `ApproximateCoordinate`: `prec_senal` (Float, default=0.0), `prec_punteria_cc` (Float, default=3.09).
- Migración: `bc697f509bb6` con `server_default` para rellenar filas existentes.

Las 18 columnas `LargeBinary` de `StationSetup` ya existían desde `142b9835b1b5` y no necesitan cambios. Tampoco se añaden las matrices a `StationSetupResponse` (son `bytes` no amigables para JSON); la exposición por API queda como **follow-up opcional**. El contrato HTTP actual (`list[ApproximateCoordinateResponse]`) se mantiene.

---

## Ficheros

**Nuevos (Etapa 1):**
- `services/calculations/least_squares_adjuster.py` — calculador MMC puro.
- `tests/test_least_squares_adjuster.py` — tests unitarios (26 casos).
- `alembic/versions/bc697f509bb6_*.py` — migración de los 4 campos de precisión.

**Modificados (Etapa 1):**
- `data/database/models/import_session.py` — `prec_dist_mm`, `prec_dist_ppm`.
- `data/database/models/approximate_coordinate.py` — `prec_senal`, `prec_punteria_cc`.
- `api/schemas/import_session_schemas.py` — exponer `prec_dist_mm`, `prec_dist_ppm`.
- `api/schemas/approximate_coordinate_schemas.py` — exponer `prec_senal`, `prec_punteria_cc`.
- `docs/PLAN_ajuste_matricial.md` — cerrar Supuesto 1, reflejar modelo de datos.

**Nuevos (Etapa 2):**
- `services/calculations/matrix_io.py` — (de)serializacion numpy<->bytes.
- `tests/test_matrix_io.py` — tests de serializacion (10 casos, incluyendo keystone).

**Pendientes (etapa siguiente):**
- `services/approximate_coordinate_service.py` — cadena MMC + persistir 18 matrices + extender `ApproximateCoordinateCalculationResult`.
- `tests/test_approximate_pipeline.py` — afirmar que las columnas de matriz quedan pobladas.

**Completados (Etapa 3):**
- `data/database/models/adjusted_coordinate.py` — modelo joined-table `AdjustedCoordinate(Coordinate)` con `bessel_observation_id`, `prec_x`, `prec_y`.
- Migración Alembic `dc205b516a81` — crea tabla `adjusted_coordinates`.
- `data/repositories/adjusted_coordinate_repository.py` — CRUD + `get_by_station_setup` + `delete_by_station_setup`.
- `api/schemas/adjusted_coordinate_schemas.py` — `AdjustedCoordinateBase`, `AdjustedCoordinateCreate`, `AdjustedCoordinateResponse`.
- `api/dependencies.py` — DI para `AdjustedCoordinateRepository` y `AdjustedCoordinateService`.
- `services/adjusted_coordinate_service.py` — `get_all`, `get_by_station_setup`, `get`, `count`.
- `api/routes/adjusted_coordinate_router.py` — `GET /`, `/by-station-setup/{id}`, `/{id}`, `/count`.
- `services/approximate_coordinate_service.py` — integración MMC: encadena `LeastSquaresAdjuster` al final del pipeline, persiste las 18 matrices y crea registros `AdjustedCoordinate`.
- `tests/test_approximate_pipeline.py` — 4 tests de integración MMC (sin/con puntos de control, matrices, idempotencia).
- `tests/test_adjusted_coordinate.py` — 5 tests de endpoints GET.
- **Verificación:** 77 tests pasan (`uv run pytest -v`).

---

## Testing

- **Unitarios del calculador** contra oráculos: construir `LsTarget` con los datos del Excel (ΔE/ΔN/dist/acimut de P1–P4) y verificar (a) los coeficientes de A, L y P coinciden con las celdas del Excel; (b) identidades algebraicas (`N=AᵀPA`, `x=N⁻¹AᵀPL`, `v=Ax−L`, `vᵀPv` coherente); (c) `red=0` no rompe y emite `warning`.
- **Pipeline:** tras `calculate_for_station_setup`, leer `StationSetup` y comprobar que las 18 columnas `*_matrix` no son `None` y `from_bytes` las decodifica con shape esperada.
- **Endpoints:** `GET /api/v1/adjusted-coordinates/by-station-setup/{id}` y `/{id}` devuelven coordenadas ajustadas con `prec_x`, `prec_y` poblados.
- **Idempotencia:** dos runs del pipeline no duplican `AdjustedCoordinate` ni matrices.

---

## Verificación (end-to-end)

1. `uv run alembic upgrade head` — crea `adjusted_coordinates`.
2. Levantar: `uv run fastapi dev main.py`.
3. Importar un `.gka` de `docs/` via `POST /api/v1/projects/import_gka/{id}` y luego `POST /api/v1/station-setups/{id}/approximate-coordinates`.
4. `GET /api/v1/adjusted-coordinates/by-station-setup/{id}` devuelve las coords ajustadas con precisiones.
5. Consultar la fila de `station_setups` en `sqlite_database/dev.db` y comprobar que `a_matrix, p_matrix, l_matrix, x_matrix, inver_n_matrix, prec_matrix, adjust_coord_matrix`, etc. estan pobladas.
6. `uv run pytest -v` — 77 tests (regresion + MMC + API).

---

## Progreso

| Etapa | Descripcion | Estado |
|-------|------------|--------|
| 1 | Modelo de precisiones + calculador puro MMC + tests | **Completada** |
| 2 | `matrix_io.py` — serializacion numpy↔bytes | **Completada** |
| 3 | Integracion en `approximate_coordinate_service` + persistencia 18 matrices + API | **Completada** |

Ver `docs/PLAN_etapa1_calculador_mmc.md` para el desglose detallado de las tareas de la Etapa 1 (T1–T7).
Ver `docs/PLAN_etapa3_integracion_mmc.md` para el desglose detallado de las tareas de la Etapa 3 (T1–T11).
