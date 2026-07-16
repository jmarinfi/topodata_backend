# Plan de Desarrollo Backend — Iteración B (detalle de tareas)

**Fecha:** 2026-07-16
**Alcance:** 1 iteración / 2 semanas
**Dedicación estimada:** ~33% jornada → **~3–4 días ideales**
**Base de partida:** commit `b943b99` (A1+A2 en master) + cambios de A3/A4 en working tree (tests en verde, 7 passing)
**Documento padre:** `Plan Backend - Próximas 2 iteraciones 2026-07-13.md`

---

## 0. Punto de partida (estado real verificado en código)

| Ítem roadmap | Estado real en el repo | Evidencia |
|---|---|---|
| A1 · Auth unificada | ✅ committed | `b943b99` (29 endpoints con `_: CurrentUser`) |
| A2 · Bugs importación | ✅ committed | `b943b99` + migración `82cf0182e30e` |
| A3 · Cablear Bessel | ⚠️ **working tree, sin commitear** | `bessel_observation_service.calculate_for_station_setup`; auto-cálculo en `import_orchestrator_service.py:91` |
| A4 · pytest + tests | ⚠️ **working tree, sin commitear** | `tests/conftest.py` + 4 tests · **7 passing** |
| **Endpoint/Bessel CRUD** | ❎ **fuera de alcance** | Bessel se calcula automático al importar GKA; sin endpoint ni CRUD |
| **B1 · Import CSV referencias** | ❎ **descartado** | Referencias por CRUD en el frontend |
| B2 · Coordenadas aproximadas | ❌ **en esta iteración** | Pipeline completo en `docs/ajustes_topografia.py`; oracles en los 3 Excel |
| B3 · Scoping por `project_id` | ❌ pendiente | Los listados de datos no filtran por `project_id` |
| Cobertura de tests | ⚠️ **parcial** | Faltan CRUD y las **cascadas de borrado de A2** |

> La Iteración A está terminada pero **sin consolidar** (A3+A4 en el working tree). El primer paso es commitearla.

---

## 1. Objetivo de la iteración

1. **B0 · Consolidar la Iteración A** (commitear A3+A4).
2. **B2 · Motor de coordenadas aproximadas** (feature central): seguir el pipeline de `docs/ajustes_topografia.py`, validado contra los 3 Excel.
3. **B3 · Scoping por `project_id`** en los listados de datos.
4. **B4 · Endurecer la suite de tests** (cascadas de A2 + CRUD).

> ⚠️ B0 + B2 + B3 + B4 superan los ~3–4 días ideales. Ver §7 para la priorización.

---

## 2. Lo que queda FUERA de esta iteración

| Ítem | Razón |
|---|---|
| Endpoint manual / CRUD de Bessel | Bessel se calcula **automáticamente al importar el GKA**; sin endpoint ni CRUD. |
| Importación CSV de referencias | Referencias por **CRUD en el frontend**. |

---

## 3. B0 — Consolidar la Iteración A · XS (0.1 d)

### B0.1 · Commitear A3+A4
- `git add` del diff actual + commit `A3+A4: cableado de Bessel al flujo de importación + suite pytest`.
- **Criterio:** `master` con A1–A4; `uv run pytest -q` verde.

---

## 4. B2 — Coordenadas aproximadas · L (≈ 2.75 d) · [Core, feature central]

### 4.1 · Aclaraciones previas

- **¿Qué es `etr_x/y/z`?** Son las **coordenadas (X, Y, Z) de la estación total / teodolito** en UTM — lo que los Excel etiquetan como *"X/Y/Z Estación total"*. No es un sistema geodésico; es el punto físico donde está apostado el instrumento.
- **Todo se calcula** siguiendo el pipeline del Colab. No hay coordenadas "dadas": la posición de la estación se obtiene por **inversa planimétrica (Cassini)**, `k_utm` por su serie, la cota `etr_z` por ángulos verticales, y a partir de ahí la desorientación y las coordenadas aproximadas.
- **Oracle numérico:** los 3 Excel (desorientación, coordenadas aproximadas, Z del estacionamiento). Todos comparten la misma estación y referencias, así que el pipeline entero es validable extremo a extremo.

### 4.2 · Pipeline (5 etapas, según `ajustes_topografia.py`)

```
Referencias (CRUD, coords UTM conocidas)  +  Observaciones Bessel (auto en import, A3)  +  RawObservation (i, m)
│
├─ (1) Inversa planimétrica de Cassini   → etr_x, etr_y        [función facilitada]
├─ (2) Factor de escala UTM (serie)      → k_utm               [a partir de etr_x/y + zona_utm]
├─ (3) Cota de la estación               → etr_z (ZEST)        [a partir de etr_x/y, k_utm, v_angle, i, m]
│     └─ persistir etr_x/y/z, k_utm en station_setup
├─ (4) Desorientación                    → desorientacion (ε)  [a partir de etr_x/y + refs + hz_bessel]
│     └─ persistir desorientacion en station_setup
└─ (5) Radiación                         → ApproximateCoordinate (x, y, z) por cada BesselObservation
      └─ persistir en approximate_coordinates
```

Dependencias: (1) → (2) → (3); (4) necesita (1); (5) necesita (1)(2)(3)(4).

### 4.3 · Oracles (entrada → valor esperado, de los Excel)

Todos usan: estación resultante **(etr_x=428254.86438, etr_y=4584084.29001)**, **k_utm=0.999663**, referencias y observaciones de las hojas.

| Etapa | Oracle (Excel) | Entradas | Salida esperada |
|---|---|---|---|
| (1) Cassini | coords "Estación total" + refs/hz de Excel 1 | ≥3 refs + `hz_angle_bessel` | **etr_x=428254.86438, etr_y=4584084.29001** |
| (2) k_utm | const. de Excel 2/3 | etr_x/y + `zona_utm` (30T) | **k_utm=0.999663** |
| (3) Z | `Cálculo de Z del estacionamiento.xlsx` | etr_x/y, k_utm, refs, v_angle, i, m | **ZEST=49.898617 m** (Z' prom=49.898549) |
| (4) Desorientación | `Cálculo desorientación.xlsx` | etr_x/y + refs + hz_bessel | **ε media=235.338413 gon** |
| (5) Coordenadas | `Cálculo coord aproximadas.xlsx` | etr_x/y/z, k_utm, ε, bessel | p.ej. C55-R-01E-C → **X=428175.188286, Y=4584168.047829, Z=43.406845** |

### 4.4 · Constantes / parámetros

**Todas las constantes del cálculo viven ya en los modelos** — no hace falta módulo de constantes ni migración.

- En `Project` (ClassVars universales): `GON_R` (π/200, gon→rad), `EARTH_RADIUS` (6 378 000), `R_CC` (2 000 000/π), `S_SEXA_CC` (250/81) y, **añadida en esta iteración**, `K_0_ADIM = 0.9996` (factor de escala UTM del meridiano central).
- En `Project` (columnas, por proyecto): `a_elip`, `b_elip`, `f_elip`, `inv_f_elip`, `zona_utm`.
- En `ImportSession` (columnas con default): `kt_coef_refr = 0.13`, `prec_ang_etr = 0.5`.
- **Derivado, no almacenado:** el paso rad→gon (acimut) se calcula como `1 / GON_R` (= 200/π).

> **Caveat del oracle (tests):** el Excel/Colab usa elipsoide **GRS80** (`inv_f=298.257222101`, `b=6356752.314`). El fixture de test debe sembrar el proyecto con esos valores exactos para reproducir `k_utm=0.999663` (el `_make_project` actual usa WGS84/redondeados).

**Mapeo de campos Colab → backend:** `i` = `station_setup.station_height` · `m` = `raw_observation.target_height` · `kt_coef_refr`/`prec_ang_etr` ← `import_session` · salidas `etr_*`, `k_utm`, `desorientacion` → `station_setup` · coordenadas → `approximate_coordinates` (x/y/z + `bessel_observation_id` existente).

### 4.5 · ⚠️ Bug de unidades a corregir al portar

El acimut se obtiene con `atan2(ΔX, ΔY)`, que devuelve **radianes**; para pasar a **gon** hay que multiplicar por **200/π** (= `1/GON_R`).
- El Excel de desorientación lo confirma: `r_gon = 63.661977 = 200/π`, y el acimut de `C55-R-01E-C` = **351.5897 gon**.
- El Colab multiplica por `gon_r` (π/200), que es el factor **inverso** (gon→rad) → valor erróneo. **Portar con `1/GON_R`**; el test lo caza.
- Ojo con el nombre: el Excel de desorientación llama `r_gon` al 200/π (rad→gon); los Excel de coord/Z llaman `gon_r` al π/200 (gon→rad, para `sin`/`cos`). **Mismo nombre, valores recíprocos, según el sentido de la conversión.**

### 4.6 · Tareas

**B2.1 · `K_0_ADIM` en `Project`** · XS (0.05) · *✅ hecho*
- Añadido `K_0_ADIM: ClassVar[float] = 0.9996` a `data/database/models/project.py`. El resto de constantes ya están (`GON_R/EARTH_RADIUS/R_CC/S_SEXA_CC` + elipsoides + `zona_utm` en `Project`; `kt_coef_refr`/`prec_ang_etr` en `ImportSession`). Sin migración.

**B2.2 · Inversa planimétrica de Cassini (etr_x, etr_y)** · S (0.3) · *✅ hecho*
- `services/calculations/station_position_calculator.py` (`StationPositionCalculator`), clase pura (sin DB), estilo `BesselAdjuster`.
- Portar `calcula_inversa_xy_cassini(x1,y1,x2,y2,x3,y3,lh1,lh2,lh3)` tal cual (usa `gon_r=π/200` para pasar `(lh2-lh1)` a rad → correcto).
- Método que promedia sobre las combinaciones de 3 refs (como `process_etr_utm`).
- **Test oracle:** con refs/hz del Excel 1 → **(428254.86438, 4584084.29001)**.

**B2.3 · Factor de escala UTM (k_utm)** · S (0.4) · *✅ hecho*
- En la misma clase, portar `calculate_k_utm` (serie desde etr_x/y + `zona_utm` + `k_0_adim`). Parsear `zona_utm` (número + letra).
- **Test oracle:** → **0.999663**.

**B2.4 · Cota de la estación (etr_z / ZEST)** · S (0.4) · *✅ hecho*
- Portar `calculate_z_est`: por cada ref, `dist_calculada=hypot(ΔE,ΔN)`, `dist_reducida=dist_calculada/k_utm`, `ΔZ'=dist_reducida·cos(v·gon_r)+(i-m)+(0.5-kt)·dist_reducida²/EARTH_RADIUS`, `Z'=z_ref-ΔZ'`; promediar; segunda pasada con reducción al elipsoide → `Z''`; `ZEST = media(Z'')`.
- `σ(α)=(prec_ang_etr·S_SEXA_CC)²` (en el Colab la ponderación se cancela → equivale a la media; mantener el código fiel al Colab y dejarlo reflejado).
- **Test oracle:** → **ZEST=49.898617**.

**B2.5 · Desorientación** · S (0.3) · *✅ hecho*
- `services/calculations/approximate_coordinate_calculator.py`. Por cada ref observada: `acimut = atan2(ref.x-etr_x, ref.y-etr_y) / GON_R` normalizado a [0,400); `ε=(acimut - hz_bessel)` normalizado; media.
- **Test oracle:** → **235.338413 gon** (per-ref C55-R-01E-C: 235.338523).

**B2.6 · Coordenadas aproximadas (radiación)** · S (0.4) · *✅ hecho*
- `w_cc=d·R_CC/EARTH_RADIUS`; `r_cc=kt·w_cc`; `dist_hor=d·sin((v-w_cc+r_cc)·GON_R)/cos((w_cc/2)·GON_R)`; `dist_elip=dist_hor·EARTH_RADIUS/(EARTH_RADIUS+etr_z)`; `dist_utm=dist_elip·k_utm`; `acimut=(hz+ε) mod 400`; `x=etr_x+dist_utm·sin(acimut·GON_R)`; `y=etr_y+dist_utm·cos(acimut·GON_R)`; `z=d·cos(v·GON_R)+(0.5-kt)·d²/EARTH_RADIUS+etr_z`.
- **Test oracle:** C55-R-01E-C → **X=428175.188286, Y=4584168.047829, Z=43.406845** (+ intermedios w=11.555028, r=1.502154, dist_utm=115.601264).

**B2.7 · Servicio `calculate_for_station_setup`** · M (0.4) · *✅ hecho*
- En `services/approximate_coordinate_service.py`, espejo de `bessel_observation_service.calculate_for_station_setup`:
  1. Cargar `station_setup` (404 si no). Cargar `BesselObservation`, `ReferenceCoordinate` del proyecto, `RawObservation` (para i/m), `Project` (constantes + `zona_utm`) e `ImportSession` (`kt_coef_refr`, `prec_ang_etr`).
  2. Validar prerequisitos: ≥3 refs observadas (Cassini) → si no, error claro.
  3. Cassini → `etr_x/y`; k_utm → `k_utm`; Z → `etr_z`; desorientación → `ε`. **Persistir** en `station_setup`.
  4. Radiar → `ApproximateCoordinate`.
  5. **Idempotencia:** `repository.delete_by_station_setup(id)` (ya existe) + reescribir.
  6. Devolver lista + warnings (p.ej. refs insuficientes).

**B2.8 · Dependencias (DI)** · XS (0.1) · *✅ hecho*
- `api/dependencies.py:get_approximate_coordinate_service`: ampliar con `StationSetupRepository`, `ProjectRepository`, `ReferenceCoordinateRepository`, `BesselObservationRepository`, `RawObservationRepository`.

**B2.9 · Endpoint** · S (0.25) · *✅ hecho*
- Las aproximadas **no pueden auto-calcularse al importar** (necesitan referencias y estación orientada, que llegan después). Trigger manual:
  ```
  POST /api/v1/station-setups/{station_setup_id}/approximate-coordinates
       → response_model=list[ApproximateCoordinateResponse], status_code=200
  ```
  `_: CurrentUser`; `try/except ValueError → 400/404`. *(Si prefieres que se calcule automáticamente cuando existan referencias, dímelo — por ahora propongo endpoint manual.)*

**B2.10 · Tests de integración** · S (0.3) · *✅ hecho*
- `tests/test_approximate_pipeline.py`: sembrar refs + bessel (del Excel) vía repos, llamar al servicio, comprobar `etr_x/y`, `k_utm`, `etr_z`, `ε` y las coordenadas contra los oracles. Cargar los valores como fixture (sin leer el `.xlsx` en el test).

**Archivos afectados (B2):** `data/database/models/project.py` (ClassVar `K_0_ADIM`); `services/calculations/station_position_calculator.py`, `approximate_coordinate_calculator.py` (nuevos); `services/approximate_coordinate_service.py`; `api/dependencies.py`; `api/routes/station_setup_router.py`; `tests/test_approximate_*.py` (nuevos). **Sin migraciones** (todas las constantes/columnas destino ya existen).

---

## 5. B3 — Scoping por `project_id` en listados de datos · M (1.5 d) · [Core]

**Jerarquía:** `project ← import_session ← station_setup ← raw/bessel ← approximate`.

| Endpoint | Filtro actual | `project_id` |
|---|---|---|
| `GET /import-sessions/`, `GET /reference-coordinates/` | ✅ ya | — |
| `GET /station-setups/` | `import_session_id` | ➕ |
| `GET /raw-observations/` | `station_setup_id` | ➕ |
| `GET /bessel-observations/` | `station_setup_id` | ➕ |
| `GET /approximate-coordinates/` | ninguno | ➕ |

- **B3.1** `get_by_project(project_id)` en los 4 repos (joins hasta `ImportSession.project_id`).
- **B3.2** `project_id: int | None` en los `GET /` y servicios (patrón `reference_coordinate_router.py:15-23`).
- **B3.3** `tests/test_project_scoping.py`: datos en 2 proyectos → cada `get_by_project` aísla.

---

## 6. B4 — Endurecer la suite de tests · M (1.3 d) · [Core]

> Cascadas hoy en servicios (sin `ON DELETE CASCADE` en DB): `ProjectService.delete_project` → `ImportSessionService.delete_import_session` → `StationSetupService.delete_station_setup` → `_delete_station_setup_children` (bulk raw+bessel+approx).

- **B4.1 · Cascadas (prioridad)** · M (0.5) — `tests/test_cascade_deletes.py`: borrar setup/sesión/proyecto → sin huérfanos; otro proyecto intacto; no existe → `ValueError`. Caso `approximate`: crearlo a mano vía repo y verificar que se borra (con su fila padre en `coordinates`).
- **B4.2 · CRUD `project`** · S (0.3) — HTTP con `auth_client`.
- **B4.3 · CRUD `import-session` + dedup** · S (0.3) — servicio: dedup de `content_hash` por proyecto.
- **B4.4 · CRUD `reference-coordinate`** · S (0.2) — servicio: `type=="reference"`; `get_by_project`.

---

## 7. Resumen, estimación y priorización

| Bloque | Días ideales | Prioridad |
|---|---|---|
| B0 · Consolidar A | 0.1 | Core |
| B2 · Coordenadas aproximadas (pipeline completo) | ≈ 2.75 | Core (feature) |
| B3 · Scoping por proyecto | 1.5 | Core |
| B4 · Endurecer tests | 1.3 | Core |
| **Total** | **≈ 5.65** | |

> Supera los ~3–4 días ideales. **Secuencia recomendada:** **B0 → B2 → B3**, y **B4** como primero en escurrirse si el cálculo (B2) consume más tiempo del previsto. (B2 está ahora plenamente oracle-backed, así que el riesgo principal es de esfuerzo, no de incertidumbre numérica.)

---

## 8. Riesgos

- **Bug de unidades del Colab** (acimut): portar con `1/GON_R`; el test de desorientación lo detecta.
- **`σ(α)` ponderación en Z:** en el Colab se cancela y equivale a la media; mantener el código fiel y dejarlo documentado para revisión del topógrafo.
- **Joins de scoping (B3):** un join mal hecho filtra de más/menos → test de 2 proyectos.
- **Cascadas fuera del servicio:** al no haber `ON DELETE CASCADE`, el contrato vive en código; B4.1 lo blinda.

---

## 9. Verificación

```bash
uv run pytest -q                      # suite verde (oracles de B2, scoping, cascadas)
uv run fastapi dev main.py            # arranque manual
```

Smoke B2: proyecto con referencias (CRUD) + GKA importado → `POST /station-setups/{id}/approximate-coordinates` → etr_x/y, k_utm, etr_z, ε y coordenadas próximas a los del Excel; recalcular = idempotente.
Smoke B3: `GET /raw-observations/?project_id=1` etc. aíslan por proyecto.
Smoke B4: borrar un proyecto → sin sesiones/observaciones huérfanas (lo cubren los tests).
