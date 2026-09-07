# TopoData Backend — Referencia Completa para Agentes LLM

> **Versión:** 2026-08-04 | **Lenguaje:** Python ≥ 3.14 | **Framework:** FastAPI | **ORM:** SQLAlchemy 2.0+ | **DB:** SQLite con Alembic

---

## 1. ESTRUCTURA DEL PROYECTO (VISTA RÁPIDA)

```
topodata_backend/
├── main.py                          # Punto de entrada FastAPI, lifespan, CORS, routers
├── create_user.py                   # Script CLI para crear usuarios (independiente)
├── pyproject.toml                   # Dependencias y configuración (uv, ruff, pytest)
├── alembic.ini                      # Configuración de migraciones Alembic
│
├── core/
│   └── config.py                    # Settings con pydantic-settings (JWT secret, etc.)
│
├── data/
│   ├── database/
│   │   ├── engine.py                # SQLAlchemy engine, SessionLocal, get_db, SessionDep
│   │   └── models/                  # Modelos ORM (SQLAlchemy Mapped)
│   │       ├── base.py              # Base (DeclarativeBase)
│   │       ├── project.py           # Project
│   │       ├── import_session.py    # ImportSession (+prec_dist_mm/ppm)
│   │       ├── station_setup.py     # StationSetup (+18 columnas matrix binarias)
│   │       ├── raw_observation.py   # RawObservation
│   │       ├── bessel_observation.py# BesselObservation
│   │       ├── coordinate.py        # Coordinate (base polimórfica joined-table)
│   │       ├── reference_coordinate.py    # ReferenceCoordinate (hereda Coordinate)
│   │       ├── approximate_coordinate.py  # ApproximateCoordinate (+prec_senal/prec_punteria_cc)
│   │       ├── adjusted_coordinate.py     # AdjustedCoordinate (hereda Coordinate) [Etapa 3]
│   │       └── user.py              # User
│   └── repositories/               # Patrón Repository sobre SQLAlchemy
│       ├── base_repository.py       # BaseRepository[ModelType] (CRUD genérico)
│       ├── project_repository.py
│       ├── import_session_repository.py
│       ├── station_setup_repository.py
│       ├── raw_observation_repository.py
│       ├── bessel_observation_repository.py
│       ├── approximate_coordinate_repository.py
│       ├── adjusted_coordinate_repository.py # [Etapa 3]
│       ├── reference_coordinate_repository.py
│       └── user_repository.py
│
├── api/
│   ├── dependencies.py              # TODAS las factorías DI → repos, services, auth
│   ├── routes/                      # Routers FastAPI (prefix /api/v1/...)
│   │   ├── project_router.py        #   /api/v1/projects + /import_gka/{id}
│   │   ├── import_session_router.py #   /api/v1/import-sessions
│   │   ├── station_setup_router.py  #   /api/v1/station-setups (+ POST .../approximate-coordinates)
│   │   ├── raw_observation_router.py#   /api/v1/raw-observations
│   │   ├── bessel_observation_router.py  # /api/v1/bessel-observations
│   │   ├── reference_coordinate_router.py# /api/v1/reference-coordinates
│   │   ├── approximate_coordinate_router.py # /api/v1/approximate-coordinates
│   │   ├── adjusted_coordinate_router.py   # /api/v1/adjusted-coordinates [Etapa 3]
│   │   └── user_router.py           #   /api/v1/auth/* + /api/v1/users
│   └── schemas/                     # Schemas Pydantic v2 (Create/Update/Response)
│       ├── project_schemas.py
│       ├── import_session_schemas.py
│       ├── station_setup_schemas.py
│       ├── raw_observaton_schemas.py #  Nota: typo en nombre de archivo
│       ├── bessel_observation_schemas.py
│       ├── coordinate_schemas.py    #   CoordinateBase polimórfico
│       ├── approximate_coordinate_schemas.py
│       ├── adjusted_coordinate_schemas.py   # [Etapa 3]
│       ├── reference_coordinate_schemas.py
│       ├── user_schemas.py          #   UserBase/Create/Update/Response + Login/Token
│       └── parser_schemas.py        #   GkaImportResult
│
├── services/
│   ├── project_service.py
│   ├── import_session_service.py
│   ├── import_orchestrator_service.py  # Orquestador de importación GKA → DB
│   ├── station_setup_service.py
│   ├── raw_observation_service.py
│   ├── bessel_observation_service.py   # Cálculo Bessel + CRUD
│   ├── approximate_coordinate_service.py # Pipeline completo + encadena MMC
│   ├── adjusted_coordinate_service.py  # [Etapa 3] Solo lectura
│   ├── reference_coordinate_service.py
│   ├── user_service.py              # Auth (register, login, CRUD usuarios)
│   ├── password_service.py          # bcrypt hash/verify
│   ├── token_service.py             # JWT encode/decode
│   ├── parsers/
│   │   ├── parser_base.py           # ABC con file_content + lines (lazy)
│   │   ├── gka_parser.py            # Parser de archivos .gka (formato Leica)
│   │   └── utils/
│   │       └── parsers_utils.py     # get_str, get_req_str, get_float, get_int, ...
│   └── calculations/
│       ├── bessel_adjuster.py                # Cálculo de promedios Bessel (pandas + numpy)
│       ├── station_position_calculator.py    # Inversa planimétrica, k_utm, ZEST
│       ├── approximate_coordinate_calculator.py # Desorientación y radiación
│       ├── least_squares_adjuster.py         # [Etapa 1] MMC puro (numpy)
│       └── matrix_io.py                      # [Etapa 2] Serialización numpy↔bytes
│
├── tests/
│   ├── conftest.py                  # Fixtures: DB SQLite en memoria, client, auth_client
│   ├── test_auth.py                 # Endpoints protegidos (401/200)
│   ├── test_gka_parser.py           # Parser GKA con ficheros reales
│   ├── test_bessel_adjuster.py      # Corrección numérica BesselAdjuster
│   ├── test_import_orchestrator.py  # Orquestador: import OK + dedup por proyecto
│   ├── test_station_position.py     # [Etapa 1] Oracles Excel: resección, k_utm, ZEST
│   ├── test_approximate_coordinate.py # [Etapa 1] Desorientación + radiación oracles
│   ├── test_approximate_pipeline.py # Pipeline completo (incluye tests MMC [Etapa 3])
│   ├── test_least_squares_adjuster.py # [Etapa 1] Tests unitarios MMC
│   ├── test_matrix_io.py            # [Etapa 2] Tests de serialización numpy
│   ├── test_adjusted_coordinate.py  # [Etapa 3] Tests HTTP de endpoints ajustados
│   ├── test_e2e_c56_excel.py        # E2E: levantamiento C56 vs Excel (HTTP real)
│   ├── test_e2e_s01_recompute.py    # E2E: levantamiento S01 por recálculo independiente
│   ├── e2e_helpers.py               # Driver HTTP + oráculos de recálculo (no es test)
│   └── bessel_tests.py              # Test manual Bessel contra DB real (no pytest)
│
├── alembic/                         # Migraciones Alembic
│   ├── env.py                       # Configuración (target_metadata = Base.metadata)
│   └── versions/
│       ├── 142b9835b1b5_*.py        # Crea columnas *_matrix en station_setups
│       ├── bc697f509bb6_*.py        # [Etapa 1] Añade prec_dist_mm/ppm y prec_senal/prec_punteria_cc
│       └── dc205b516a81_*.py        # [Etapa 3] Crea tabla adjusted_coordinates
│
├── docs/                            # Ficheros .gka + oráculos de cálculo + planes
│   ├── 20250829_013022_20250829_013939.gka   # 1 estacionamiento (parser/import)
│   ├── 20251112_200023_20251112_210627.gka   # 4 estacionamientos (S01, E2E recálculo)
│   ├── 20260121_*.gka               # Levantamiento C56 (1 estacionamiento, E2E vs Excel)
│   ├── ajustes_topografia.py        # Implementación independiente del Colab (oráculo)
│   ├── Cálculo coord aproximadas.xlsx / Cálculo desorientación.xlsx / Cálculo de Z del estacionamiento.xlsx
│   ├── Pasos de cálculo v1.pdf      # Procedimiento de cálculo de referencia
│   ├── matrices/                    # Excel de especificación del MMC
│   ├── PLAN_ajuste_matricial.md     # Plan general del ajuste MMC
│   ├── PLAN_etapa1_calculador_mmc.md
│   ├── PLAN_etapa2_matrix_io.md
│   └── PLAN_etapa3_integracion_mmc.md
│
└── sqlite_database/                 # Directorio de la DB SQLite (dev.db)
```

---

## 2. ARQUITECTURA EN CAPAS

```
┌─────────────────────────────────────────────┐
│  API (routes + schemas)                     │  ← Presentación
│  api/routes/*  →  endpoints HTTP            │
│  api/schemas/* →  validación Pydantic v2    │
├─────────────────────────────────────────────┤
│  api/dependencies.py                        │  ← DI (Factorías)
│  Todas las dependencias tipadas con Annotated│
├─────────────────────────────────────────────┤
│  services/*                                 │  ← Lógica de negocio
│  Orquestación, CRUD, auth, cálculo Bessel, MMC │
├─────────────────────────────────────────────┤
│  data/repositories/*                        │  ← Acceso a datos
│  Patrón Repository (BaseRepository[T])      │
├─────────────────────────────────────────────┤
│  data/database/models/*                     │  ← Modelos ORM
│  SQLAlchemy 2.0 Mapped + DeclarativeBase    │
└─────────────────────────────────────────────┘
```

**Principios clave:**
- **Inyección de dependencias:** Todo pasa por `api/dependencies.py`. Los routers NUNCA instancian servicios/repos directamente. Usan los tipos `Annotated` (ej: `ProjectServiceDep`, `AdjustedCoordinateServiceDep`).
- **Cascada de borrado manual:** NO se usa `cascade` de SQLAlchemy. El borrado en cascada es explícito en los services (ej: `StationSetupService._delete_station_setup_children` → bulk delete).
- **Validación en schemas:** `ProjectBase.populate_geodetic_parametrs` usa `pyproj` para derivar parámetros del elipsoide desde el código EPSG.

---

## 3. CATÁLOGO DE CLASES, FUNCIONES Y MÓDULOS

### 3.1. Modelos ORM (`data/database/models/`)

| Modelo | Tabla | PK | FK → | Notas |
|--------|-------|----|------|-------|
| `Project` | `projects` | `id` | — | Parámetros elipsoidales (`a_elip`, `b_elip`, `f_elip`, `inv_f_elip`), constantes de clase (`GON_R`, `EARTH_RADIUS`, etc.) |
| `ImportSession` | `import_sessions` | `id` | `project_id → projects.id` | UniqueConstraint(`project_id`, `content_hash`). Atributos `kt_coef_refr`, `prec_ang_etr`, `prec_dist_mm` (Etapa 1), `prec_dist_ppm` (Etapa 1). Almacena el contenido completo del fichero importado en `raw_file_content` (Text). |
| `StationSetup` | `station_setups` | `id` | `import_session_id → import_sessions.id` | Columnas de cálculo (`etr_x/y/z`, `k_utm`, `desorientacion`) y **18 columnas `LargeBinary`** para matrices MMC (v, a, tra_a, p, tra_a_p, x, l, n, inver_n, t, tra_v_p, desv_post, var_post, num_equations, num_unknowns, inter_conf, prec, adjust_coord) |
| `RawObservation` | `raw_observations` | `id` | `station_setup_id → station_setups.id` | Ángulos en **gon** (grados centesimales). `circle ∈ {1, 2}` |
| `BesselObservation` | `bessel_observations` | `id` | `station_setup_id → station_setups.id` | 12 columnas: directo, inverso, bessel, delta para hz/v/dist |
| `Coordinate` | `coordinates` | `id` | — | **Polimórfica** (joined-table inheritance). Discriminador: `type` |
| `ApproximateCoordinate` | `approximate_coordinates` | `id` (FK→coordinates) | `bessel_observation_id → bessel_observations.id` | Hereda de `Coordinate`. `polymorphic_identity="approximate"`. Campos MMC: `prec_senal` (Float, default=0.0), `prec_punteria_cc` (Float, default=3.09) — Etapa 1 |
| `AdjustedCoordinate` | `adjusted_coordinates` | `id` (FK→coordinates) | `bessel_observation_id → bessel_observations.id` | **Etapa 3**. Hereda de `Coordinate`. `polymorphic_identity="adjusted"`. Campos propios: `prec_x`, `prec_y`. |
| `ReferenceCoordinate` | `reference_coordinates` | `id` (FK→coordinates) | `project_id → projects.id` | Hereda de `Coordinate`. `polymorphic_identity="reference"` |
| `User` | `users` | `id` | — | `username` unique, `email` unique, `hashed_password`, `is_active`, `is_superuser` |

### 3.2. Repositorios (`data/repositories/`)

**Clase base:** `BaseRepository[ModelType]` — métodos: `get(id)`, `get_all()`, `count()`, `create(attributes)`, `update(db_obj, attributes)`, `delete(db_obj)`, `refresh(db_obj)`.

| Repositorio | Modelo | Métodos extra |
|-------------|--------|--------------|
| `ProjectRepository` | `Project` | — |
| `ImportSessionRepository` | `ImportSession` | `get_by_project(project_id)`, `get_by_project_and_hash(project_id, content_hash)` |
| `StationSetupRepository` | `StationSetup` | `get_by_import_session(import_session_id)` |
| `RawObservationRepository` | `RawObservation` | `get_by_station_setup(id)`, `delete_by_station_setup(id)` (bulk) |
| `BesselObservationRepository` | `BesselObservation` | `get_by_station_setup(id)`, `delete_by_station_setup(id)` (bulk) |
| `ApproximateCoordinateRepository` | `ApproximateCoordinate` | `get_by_bessel_observation(id)`, `get_by_station_setup(id)`, `delete_by_station_setup(id)` (bulk, borra también la fila padre `Coordinate`) |
| `AdjustedCoordinateRepository` | `AdjustedCoordinate` | **Etapa 3**. `get_by_bessel_observation(id)`, `get_by_station_setup(id)`, `delete_by_station_setup(id)` (bulk, joined-table) |
| `ReferenceCoordinateRepository` | `ReferenceCoordinate` | `get_by_project(project_id)` |
| `UserRepository` | `User` | `get_by_username(name)`, `get_by_email(email)`, `exists_by_username(name)`, `exists_by_email(email)` |

### 3.3. Servicios (`services/`)

| Servicio | Dependencias (repos) | Métodos clave |
|----------|---------------------|---------------|
| `ProjectService` | `ProjectRepository`, `ImportSessionRepository`, `ImportSessionService`, `ReferenceCoordinateService` | `get_projects()`, `get_project(id)`, `create_project(data)`, `update_project(id,data)`, `delete_project(id)` (cascada manual: sessions vía `ImportSessionService` + ref coords vía `ReferenceCoordinateService`) |
| `ImportSessionService` | `ImportSessionRepository`, `ProjectRepository`, `StationSetupRepository`, `StationSetupService` | `get_import_sessions()`, `get_by_project(pid)`, `create` (valida proyecto + hash único), `delete` (cascada vía `StationSetupService`) |
| `StationSetupService` | `StationSetupRepository`, `ImportSessionRepository`, `RawObservationRepository`, `BesselObservationRepository`, `ApproximateCoordinateRepository` | `_delete_station_setup_children(id)` (bulk: approx → bessel → raw, en orden) |
| `RawObservationService` | `RawObservationRepository`, `StationSetupRepository` | CRUD estándar |
| `BesselObservationService` | `BesselObservationRepository`, `StationSetupRepository`, `RawObservationRepository`, `ApproximateCoordinateRepository` | **`calculate_for_station_setup(id) → BesselCalculationResult`** (idempotente, fallo suave) |
| `ApproximateCoordinateService` | `ApproximateCoordinateRepository`, `BesselObservationRepository`, `StationSetupRepository`, `ProjectRepository`, `ReferenceCoordinateRepository`, `RawObservationRepository`, `ImportSessionRepository`, **`AdjustedCoordinateRepository`** (Etapa 3) | CRUD estándar + `get_by_bessel_observation(id)` + `get_by_station_setup(id)` + **`calculate_for_station_setup(id) → ApproximateCoordinateCalculationResult`**: pipeline completo (Bessel → Cassini → k_utm → ZEST → desorientación → radiación → **MMC**) que persiste 18 matrices en `StationSetup` y crea `AdjustedCoordinate` por punto de control. **Idempotente.** |
| `AdjustedCoordinateService` | `AdjustedCoordinateRepository`, `StationSetupRepository` | **Etapa 3**. Solo lectura: `get_all()`, `get_by_station_setup(id)` (valida estacionamiento), `get(id)`, `count()`. |
| `ReferenceCoordinateService` | `ReferenceCoordinateRepository`, `ProjectRepository` | CRUD estándar + `get_by_project(id)` |
| `ImportOrchestratorService` | `ImportSessionRepository`, `StationSetupRepository`, `RawObservationRepository`, `BesselObservationService` | **`process_gka_import(project_id, filename, file_content) → GkaImportResult`** |
| `UserService` | `UserRepository`, `PasswordService`, `TokenService` | `register(data)`, `login(credentials) → TokenResponse`, `update_user(id, data)` |
| `PasswordService` | — | `hash(plain) → str`, `verify(plain, hashed) → bool` (bcrypt) |
| `TokenService` | — | `create_access_token(user_id, username) → str`, `decode_token(token) → TokenPayload` (pyjwt) |

### 3.4. Parsers (`services/parsers/`)

| Clase | Archivo | Hereda de | Propósito |
|-------|---------|-----------|-----------|
| `ParserBase` | `parser_base.py` | `ABC` | `file_content`, `lines` (lazy property), `parse()` abstracto |
| `GkaParser` | `gka_parser.py` | `ParserBase` | Parsea archivos `.gka` (formato Leica GNV11). Detecta bloques `#GNV11`...`#END11`. Extrae `StationSetupParsed` + lista de `RawObservationParsed`. Usa `gps_time` para convertir GPS week/TOW a datetime. |
| `GkaParserResult` | `gka_parser.py` | `dataclass` | `station: StationSetupParsed`, `raw_observations: list[RawObservationParsed]` |
| `parsers_utils` | `utils/parsers_utils.py` | — | `get_str`, `get_req_str`, `get_float`, `get_req_float`, `get_int`, `get_req_int` (extracción segura de columnas CSV) |

### 3.5. Cálculos (`services/calculations/`)

| Clase | Archivo | Propósito |
|-------|---------|-----------|
| `BesselAdjuster` | `bessel_adjuster.py` | **`adjust_bessel() → list[BesselObservationCreate]`**. Toma `StationSetupResponse` + `list[RawObservationResponse]`, filtra observaciones con `v_angle≠0` y `distance_geom≠0`, pivotea por `target_name` y `circle` (1=directo, 2=inverso), y calcula promedios Bessel. Usa **pandas** (`pivot_table`) + **numpy** (`np.where`). |
| `StationPositionCalculator` | `station_position_calculator.py` | **Inversa planimétrica de Cassini** (método de instancia) → coordenadas `etr_x`, `etr_y`. **Factor de escala UTM** `k_utm` (método estático). **Cota de la estación** `etr_z` (ZEST) por ángulos verticales con reducción al elipsoide. |
| `ApproximateCoordinateCalculator` | `approximate_coordinate_calculator.py` | **Desorientación del estacionamiento** (B2.5): calcula el promedio de acimutes a referencias conocidas. **Radiación de coordenadas** (B2.6): proyecta cada observación Bessel desde la estación para obtener coordenadas aproximadas. |
| `LeastSquaresAdjuster` | `least_squares_adjuster.py` | **Etapa 1**. Ajuste por mínimos cuadrados (MMC) puro. Cadena `A → Aᵀ → P → AᵀP → N=AᵀPA → N⁻¹ → t=AᵀPL → x=N⁻¹t → v=Ax−L → σ̂² → precisiones → coords ajustadas`. **Instanciado** (no métodos estáticos), toma dataclasses (`LsTarget`) + primitivos, devuelve `LeastSquaresResult`, lanza `ValueError`. Estación fija, incógnitas `dx, dy` de cada punto visado. Si `redundancy ≤ 0`, `var_post=desv_post=0`, `prec` a 0, añade `warning`. |
| `matrix_io` | `matrix_io.py` | **Etapa 2**. (De)serialización numpy↔bytes: `to_bytes(arr) → bytes` (`.npy`), `from_bytes(b) → ndarray` (sin pickle), `scalar_to_bytes(x) / scalar_from_bytes(b)`. Usado para persistir las 18 matrices del MMC en columnas `LargeBinary` de `StationSetup`. |

**Dataclasses auxiliares de cálculo:**

| Dataclass | Archivo | Propósito |
|-----------|---------|-----------|
| `ResectionResult` | `station_position_calculator.py` | `etr_x`, `etr_y`, `combinations` (nº de tríos válidos) |
| `ZEstResult` | `station_position_calculator.py` | `z_est` (cota final), `z_prima_mean` (cota media), `combinations` |
| `DesorientacionResult` | `approximate_coordinate_calculator.py` | `desorientacion`, `combinations` |
| `RadiacionResult` | `approximate_coordinate_calculator.py` | `target_name`, `x`, `y`, `z` + intermedios (`w_cc`, `r_cc`, `dist_hor`, `dist_elip`, `dist_utm`, `acimut`) |
| `LsTarget` | `least_squares_adjuster.py` | **Etapa 1**. Observación de un punto para el MMC: `target_name, approx_x, approx_y, dist_utm, acimut_observado, prec_senal, prec_punteria_cc`. |
| `LeastSquaresResult` | `least_squares_adjuster.py` | **Etapa 1**. Arrays numpy (`sigma_dir, sigma_dist, a, tra_a, p, tra_a_p, l, n, inver_n, t, x, v, tra_v_p`), escalares (`num_equations, num_unknowns, redundancy, var_post, desv_post, inter_conf`), `prec` (array 2k) y `adjusted_coords` (`list[(target_name, x, y)]`) + `warnings`. |
| `ApproximateCoordinateCalculationResult` | `approximate_coordinate_service.py` | `approximate_coordinates`, `etr_x/y/z`, `k_utm`, `desorientacion`, `warnings` + **Etapa 3**: `adjusted_coordinates: list[AdjustedCoordinateResponse]`, `desv_post`, `num_equations`, `num_unknowns`, `redundancy` |

**Constante global:** `INTER_CONF_DEFAULT = 1.9599639845400536` (z al 95 %, usada por defecto en `LeastSquaresAdjuster`).

**Fórmulas Bessel (gon):**

$$
\text{hz\_bessel} = \frac{\text{hz\_direct} + \text{hz\_inverse} \pm 200}{2}, \quad \text{signo: } -200 \text{ si hz\_direct} < 200, +200 \text{ sino}
$$

$$
\text{v\_bessel} = \text{v\_direct} - \frac{\text{v\_direct} + \text{v\_inverse} - 400}{2}
$$

$$
\text{distance\_bessel} = \frac{\text{distance\_direct} + \text{distance\_inverse}}{2}
$$

**Fórmulas del MMC (Etapa 1, `least_squares_adjuster.py`):**

Por cada punto `i` con coords aproximadas `(x_i, y_i)`, distancia observada `dist_utm_i`, acimut observado `acim_i`:

```
ΔE = x_i − etr_x,  ΔN = y_i − etr_y
dist_calc = hypot(ΔE, ΔN)
acim_calc = atan2(ΔE, ΔN) / GON_R   (normalizado a [0, 400))

# Matriz A (filas: N direcciones + N distancias; columnas: dx_i, dy_i)
Fila dirección, col dx_i:   ΔN · R_CC / dist_calc²
Fila dirección, col dy_i:   −ΔE · R_CC / dist_calc²
Fila distancia,  col dx_i:   ΔE / dist_utm
Fila distancia,  col dy_i:   ΔN / dist_utm

# Matriz L (miscierre)
Dirección:  −(acim_calc − acim_obs) · 10000     [cc]
Distancia:  −(dist_calc − dist_utm)              [m]

# Precisiones a priori (σ a priori por observación)
σ_ang_cc_i = sqrt( (prec_ang_etr · S_SEXA_CC)² + (prec_senal_i/dist_utm_i · R_CC)² + prec_punteria_cc_i² )
σ_dist_m_i = sqrt( prec_senal_i² + (prec_dist_mm/1000 + prec_dist_ppm·1e-6 · dist_utm_i)² )

# Peso (P diagonal)
peso_dir_i   = 1 / σ_ang_cc_i²
peso_dist_i  = 1 / σ_dist_m_i²

# Cadena MMC
N = Aᵀ·P·A;   N⁻¹;   x = N⁻¹·Aᵀ·P·L;   v = A·x − L
σ̂² = (vᵀ·P·v) / (num_eq − num_unk)        # solo si redundancia > 0
prec_i = σ̂ · INTER_CONF · sqrt(N⁻¹[i,i])
coord_ajustada_i = coord_aprox_i + x_i
```

### 3.6. Schemas Pydantic (`api/schemas/`)

**Convención de nombres:**
- `XxxBase` → campos comunes
- `XxxCreate` → hereda de Base, añade FKs obligatorias
- `XxxUpdate` → hereda de Create/Base, para PUT (todos los campos requeridos)
- `XxxResponse` → añade `id`, `model_config = ConfigDict(from_attributes=True)`
- `XxxParsed` → sólo para datos parseados desde archivos (no tiene FK)
- `GkaImportResult` → schema compuesto: `import_session + station_setups + raw_observations + warnings`

**Schemas notables:**
- `ProjectBase.populate_geodetic_parametrs` — `@model_validator(mode="before")` que usa `pyproj.CRS` para derivar `a_elip`, `b_elip`, `f_elip`, `inv_f_elip` desde el `coordinate_system` (código EPSG).
- `CoordinateBase` — base polimórfica con campo `type: Literal["coordinate"]`
- `TokenPayload` — `sub: int` (user id), `username: str`, `exp: datetime`
- `AdjustedCoordinateBase` (Etapa 3) — extiende `CoordinateBase` con `bessel_observation_id`, `prec_x`, `prec_y`.
- `ApproximateCoordinateCreate` (Etapa 1+) — incluye `prec_senal`, `prec_punteria_cc` (persistidos y restaurados en recálculos).
- `ImportSessionCreate` (Etapa 1+) — incluye `prec_dist_mm`, `prec_dist_ppm` (defaults 0.8 y 1).

### 3.7. Dependencias Inyectables (`api/dependencies.py`)

Todas las dependencias siguen el patrón:
1. **Función factory** → `get_xxx_repository(db: SessionDep)` / `get_xxx_service(repo: XxxDep, ...)`
2. **Alias tipado** → `XxxDep = Annotated[Xxx, Depends(get_xxx)]`

**Dependencias disponibles para usar en routers:**

| Alias | Tipo |
|-------|------|
| `SessionDep` | `Annotated[Session, Depends(get_db)]` |
| `ProjectServiceDep` | `ProjectService` |
| `ImportSessionServiceDep` | `ImportSessionService` |
| `StationSetupServiceDep` | `StationSetupService` |
| `RawObservationServiceDep` | `RawObservationService` |
| `BesselObservationServiceDep` | `BesselObservationService` |
| `ApproximateCoordinateServiceDep` | `ApproximateCoordinateService` |
| `AdjustedCoordinateServiceDep` | **`AdjustedCoordinateService`** (Etapa 3) |
| `ReferenceCoordinateServiceDep` | `ReferenceCoordinateService` |
| `ImportOrchestratorServiceDep` | `ImportOrchestratorService` |
| `UserServiceDep` | `UserService` |
| `ProjectRepositoryDep` | `ProjectRepository` |
| `ImportSessionRepositoryDep` | `ImportSessionRepository` |
| `StationSetupRepositoryDep` | `StationSetupRepository` |
| `RawObservationRepositoryDep` | `RawObservationRepository` |
| `BesselObservationRepositoryDep` | `BesselObservationRepository` |
| `ApproximateCoordinateRepositoryDep` | `ApproximateCoordinateRepository` |
| `AdjustedCoordinateRepositoryDep` | **`AdjustedCoordinateRepository`** (Etapa 3) |
| `ReferenceCoordinateRepositoryDep` | `ReferenceCoordinateRepository` |
| `UserRepositoryDep` | `UserRepository` |
| `CurrentUser` | `UserResponse` (extraído del token JWT) |
| `OAuth2Dep` | `str` (token crudo) |

### 3.8. Rutas API (`api/routes/`)

| Router | Prefijo | Tag | Endpoints |
|--------|---------|-----|-----------|
| `project_router` | `/api/v1/projects` | `projects` | `GET /`, `/count`, `/{id}`, `/{id}/name`, `POST /`, `PUT /{id}`, `DELETE /{id}` (204), `POST /import_gka/{id}` (upload .gka) |
| `import_session_router` | `/api/v1/import-sessions` | `import-sessions` | `GET /?project_id=`, `/count`, `/{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}` (204) |
| `station_setup_router` | `/api/v1/station-setups` | `station-setups` | `GET /?import_session_id=`, `/count`, `/{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}` (204), **`POST /{id}/approximate-coordinates`** (dispara pipeline completo: Bessel + Cassini + k_utm + ZEST + desorientación + radiación + MMC) |
| `raw_observation_router` | `/api/v1/raw-observations` | `raw-observations` | `GET /?station_setup_id=`, `/count`, `/{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}` (204) |
| `bessel_observation_router` | `/api/v1/bessel-observations` | `bessel-observations` | `GET /?station_setup_id=`, `/count`, `/{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}` (204) |
| `approximate_coordinate_router` | `/api/v1/approximate-coordinates` | `approximate-coordinates` | `GET /`, `/by-station-setup/{id}`, `/by-bessel-observation/{id}`, `/count`, `/{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}` (204) |
| `adjusted_coordinate_router` | `/api/v1/adjusted-coordinates` | `adjusted-coordinates` | **Etapa 3**. **Solo lectura**: `GET /`, `/by-station-setup/{id}`, `/{id}`, `/count` (todos con `_: CurrentUser`). |
| `reference_coordinate_router` | `/api/v1/reference-coordinates` | `reference-coordinates` | `GET /?project_id=`, `/count`, `/{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}` (204) |
| `user_router` | `/api/v1` | `auth` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /users`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}` (204) |

**Patrón de todos los routers:**
- Todos los endpoints requieren `_: CurrentUser` (autenticación JWT), excepto `register` y `login`.
- Usan `HTTPException(status_code=404, detail=str(e))` para errores de dominio.
- Usan `HTTPException(status_code=400, detail=str(e))` para errores de validación de negocio.

---

## 4. FLUJO DE IMPORTACIÓN GKA (EL FLUJO PRINCIPAL)

```
POST /api/v1/projects/import_gka/{project_id}
    │
    ▼
project_router.import_gka()
    │  valida extensión .gka y encoding UTF-8
    ▼
ImportOrchestratorService.process_gka_import(project_id, filename, file_content)
    │
    ├─1. GkaParser(file_content).parse() → list[GkaParserResult]
    │     └─ Cada bloque #GNV11..#END11 produce un GkaParserResult
    │        con StationSetupParsed + list[RawObservationParsed]
    │
    ├─2. hashlib.sha256(file_content) → content_hash
    │     └─ Deduplicación: si ya existe (project_id, content_hash) → ValueError
    │
    ├─3. ImportSessionRepository.create(...) → import_session
    │
    ├─4. Para cada GkaParserResult:
    │     ├─ StationSetupRepository.create(station_dict) → station
    │     ├─ Para cada RawObservationParsed:
    │     │    └─ RawObservationRepository.create(obs_dict) → raw_obs
    │     └─ BesselObservationService.calculate_for_station_setup(station.id)
    │          └─ Si falla (sin pares directo/inverso) → warning (no aborta)
    │
    └─5. Retorna GkaImportResult(import_session, station_setups, raw_observations, warnings)
```

### 4.1. Flujo del pipeline de coordenadas aproximadas + MMC

Disparado por `POST /api/v1/station-setups/{id}/approximate-coordinates` o directamente desde `ApproximateCoordinateService.calculate_for_station_setup(id)`:

```
1. Cargar entidades (station_setup, import_session, project, bessel_obs, raw_obs, refs)
   └─ ValueError si falta alguna o refs < 3

2. Resección Cassini → (etr_x, etr_y)
   StationPositionCalculator(...).calculate_resection()

3. k_utm = StationPositionCalculator.calculate_k_utm(etr_x, etr_y, zona_utm, ...)

4. ZEST → etr_z
   StationPositionCalculator.calculate_z_est(...)

5. Desorientación (ε) del estacionamiento
   ApproximateCoordinateCalculator.calculate_desorientacion(...)

6. Radiación → list[RadiacionResult] (target_name, x, y, z, dist_utm, acimut, ...)
   ApproximateCoordinateCalculator.calculate_all_radiaciones(...)
   Cadena V2 (Excel v2): reducción al horizonte con conversión cc→gon
   —numerador v + (r−w)/10000, denominador w/20000; 1 gon = 10000 cc—,
   luego elipsoide y plano UTM; la cota z lleva el término +i−m
   (i = station_height, m = target_height de la primera obs cruda del objetivo)

─── Etapa 3: MMC ─────────────────────────────────────────────
7. Capturar prec_by_target de ApproximateCoordinate previos
   (prec_senal, prec_punteria_cc) por target_name

8. control_radiaciones = radiaciones − {referencias}
   Si vacío → warning "MMC omitido", saltar a paso 12

9. LeastSquaresAdjuster(etr_x, etr_y, LsTarget[], ...).calculate()
   └─ Si ValueError → warning, ls_result = None

10. Persistir en StationSetup (un único update):
    {etr_x, etr_y, etr_z, k_utm, desorientacion} +
    13 arrays MMC (to_bytes) +
    5 escalares MMC (scalar_to_bytes)

11. delete_by_station_setup en ApproximateCoordinateRepository
                        + AdjustedCoordinateRepository
─────────────────────────────────────────────────────────────

12. Recrear ApproximateCoordinate preservando prec_senal/prec_punteria_cc

13. Crear AdjustedCoordinate por cada punto de control único
    (x, y ajustados; z arrastrado del RadiacionResult; prec_x, prec_y del resultado)

14. Return ApproximateCoordinateCalculationResult(
        approximate_coordinates, adjusted_coordinates,
        etr_x/y/z, k_utm, desorientacion,
        desv_post, num_equations, num_unknowns, redundancy,
        warnings
    )
```

---

## 5. JERARQUÍA DE ENTIDADES (CASCADA DE BORRADO)

```
Project
 └─ ImportSession (cascada manual en ProjectService.delete_project)
      └─ StationSetup (cascada manual en ImportSessionService.delete_import_session)
           ├─ RawObservation (bulk delete en StationSetupService._delete_station_setup_children)
           ├─ BesselObservation (bulk delete)
           ├─ ApproximateCoordinate → Coordinate (bulk delete, joined-table)
           └─ AdjustedCoordinate → Coordinate (bulk delete, joined-table)  [Etapa 3]
```

**IMPORTANTE:** El borrado es **siempre manual y explícito**. NO se usa `cascade="all, delete-orphan"` de SQLAlchemy. Cada service tiene su propio método de borrado que propaga hacia abajo.

---

## 6. AUTENTICACIÓN Y AUTORIZACIÓN

- **Esquema:** OAuth2 Password Bearer (`/api/v1/auth/login` → JWT)
- **Flujo:**
  1. `POST /auth/register` → crea usuario (contraseña hasheada con bcrypt)
  2. `POST /auth/login` → valida credenciales → devuelve `{access_token, token_type: "bearer"}`
  3. Requests subsiguientes: `Authorization: Bearer <token>`
  4. `get_current_user` en `dependencies.py` decodifica el JWT, busca el usuario en DB, devuelve `UserResponse`
- **JWT payload:** `{"sub": user_id_str, "username": str, "exp": timestamp}`
- **Configuración JWT:** `core/config.py` → `Settings` (desde `.env`): `secret_key`, `algorithm=HS256`, `access_token_expire_minutes=60`
- **Endpoints públicos:** `POST /auth/register`, `POST /auth/login`
- **Endpoints protegidos:** Todos los demás → requieren `_: CurrentUser`

---

## 7. BASE DE DATOS

- **Motor:** SQLite (`sqlite:///./sqlite_database/dev.db`)
- **Conexión:** `check_same_thread=False` (requerido para FastAPI async)
- **Sesiones:** `SessionLocal` con `autocommit=False`, `autoflush=False`, `expire_on_commit=False`
- **Inyección:** `get_db()` → generador que hace commit en éxito, rollback en excepción
- **Alias:** `SessionDep = Annotated[Session, Depends(get_db)]`
- **Migraciones:** Alembic (`alembic upgrade head`), modelos registrados en `data.database.models.__init__`
- **Migraciones relevantes:**
  - `142b9835b1b5` — añade las 18 columnas `*_matrix` a `station_setups` (vacías, sin uso aún).
  - `bc697f509bb6` — **Etapa 1**: añade `prec_dist_mm`/`prec_dist_ppm` a `import_sessions` y `prec_senal`/`prec_punteria_cc` a `approximate_coordinates` con `server_default` para filas existentes.
  - `dc205b516a81` — **Etapa 3**: crea tabla `adjusted_coordinates` (joined-table).

---

## 8. CONFIGURACIÓN

- **Archivo:** `core/config.py` → `Settings(BaseSettings)` con `model_config = SettingsConfigDict(env_file=".env")`
- **Variables:** `secret_key` (requerida, sin ella la app no arranca), `algorithm` (default HS256), `access_token_expire_minutes` (default 60)
- **Archivo `.env`:** Debe existir en la raíz del proyecto. Ejemplo mínimo:
  ```env
  SECRET_KEY="clave-secreta-de-al-menos-32-caracteres"
  ALGORITHM="HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES=120
  ```
- **Singleton:** `settings = Settings()` (global, se imprime al importar)
- **Generar SECRET_KEY:** `openssl rand -base64 32`

---

## 9. DEPENDENCIAS EXTERNAS CLAVE

| Paquete | Uso |
|---------|-----|
| `fastapi[standard]` | Framework web |
| `sqlalchemy>=2.0.47` | ORM (estilo 2.0 con `Mapped`) |
| `alembic` | Migraciones de DB |
| `pydantic-settings` | Configuración desde `.env` |
| `pydantic` (v2) | Validación de datos (viene con FastAPI) |
| `bcrypt` | Hash de contraseñas |
| `pyjwt` | Tokens JWT |
| `pyproj` | Derivar parámetros de elipsoide desde EPSG |
| `pandas` + `numpy` | Cálculos Bessel y MMC (pivot_table, operaciones vectorizadas, `np.linalg.inv`) |
| `gps-time` | Conversión GPS week/TOW → datetime |
| `pytest` + `httpx` | Testing |

---

## 10. TESTS

- **Framework:** pytest (config en `pyproject.toml`: `testpaths = ["tests"]`, `pythonpath = ["."]`)
- **Fixtures clave en `conftest.py`:**
  - `db_session` → sesión SQLAlchemy directa sobre SQLite en memoria (para tests de servicio)
  - `client` → `TestClient` con `get_db` sobreescrito a DB en memoria
  - `auth_client` → `client` con token JWT (usuario `tester` registrado y autenticado)
- **Tests existentes (86 totales):**
  - `test_auth.py` → 401 sin token, 200 con token
  - `test_gka_parser.py` → parseo de 1 estación y 4 estaciones
  - `test_bessel_adjuster.py` → par sintético directo+inverso, error sin par inverso
  - `test_import_orchestrator.py` → import OK + deduplicación por proyecto
  - `test_station_position.py` → **Etapa 1**: oracles Excel de resección, k_utm, ZEST
  - `test_approximate_coordinate.py` → **Etapa 1**: oracles de desorientación y radiación
  - `test_approximate_pipeline.py` → Pipeline completo + **Etapa 3**: integración MMC (`TestMMCIntegration`)
  - `test_least_squares_adjuster.py` → **Etapa 1**: tests unitarios MMC (identidades algebraicas, redundancia, etc.)
  - `test_matrix_io.py` → **Etapa 2**: round-trip numpy↔bytes
  - `test_adjusted_coordinate.py` → **Etapa 3**: tests HTTP de `GET /api/v1/adjusted-coordinates/*`
  - `test_e2e_c56_excel.py` → **E2E**: importa el levantamiento C56 por HTTP y verifica cada etapa contra los Excel (resección, k_utm, ZEST, desorientación, radiación, MMC sobre los 3 controles)
  - `test_e2e_s01_recompute.py` → **E2E**: importa el levantamiento S01 (4 estacionamientos) por HTTP y verifica cada etapa por recálculo independiente + comprueba el álgebra de las matrices MMC persistidas (`TestE2ES01MmcMatrices`)
  - `e2e_helpers.py` → helpers compartidos de los E2E (driver HTTP + oráculos de recálculo); no sigue el patrón `test_*` así que pytest no lo recoge
  - `bessel_tests.py` → test manual (no pytest) contra DB real

---

## 11. CONVENCIONES DE CÓDIGO

- **Idioma:** Código y comentarios en **español** (excepto keywords de Python)
- **Typing completo:** TODO tiene type hints (mypy-friendly, `Mapped`, `Annotated`)
- **Docstrings:** En español, estilo Google/NumPy
- **Nombres de atributos de modelo:** snake_case (ej: `hz_angle_direct`, `station_setup_id`)
- **Nombres de columnas en DB:** igual que el atributo Python (SQLAlchemy lo infiere)
- **Manejo de errores:** `ValueError` en services → `HTTPException` en routers
- **Formateo:** Ruff configurado con `ignore = ["RUF032"]`

---

## 12. PATRONES DE USO COMÚN PARA EL AGENTE

### ¿Cómo empezar desde cero en una máquina nueva?
1. `git clone` + `uv sync`
2. Crear archivo `.env` con `SECRET_KEY` (generar con `openssl rand -base64 32`)
3. `uv run alembic upgrade head`
4. `uv run python create_user.py` (crear primer usuario)
5. `uv run fastapi dev main.py`

### ¿Cómo añadir un nuevo endpoint?
1. Crear/esquema en `api/schemas/`
2. Añadir método al service correspondiente en `services/`
3. Si necesita nuevo acceso a datos, añadir método al repository en `data/repositories/`
4. Añadir endpoint al router en `api/routes/`
5. Si el service es nuevo, registrarlo en `api/dependencies.py`

### ¿Cómo añadir un nuevo modelo?
1. Crear archivo en `data/database/models/`
2. Heredar de `Base`
3. Registrar en `data/database/models/__init__.py`
4. Crear repositorio en `data/repositories/` (heredar de `BaseRepository`)
5. Registrar en `data/repositories/__init__.py`
6. Crear migración: `uv run alembic revision --autogenerate -m "descripción"`
7. Aplicar: `uv run alembic upgrade head`

### ¿Cómo añadir un nuevo formato de archivo de importación?
1. Crear parser en `services/parsers/` (heredar de `ParserBase`)
2. Implementar `parse()` que devuelva datos parseados
3. Añadir orquestación en `ImportOrchestratorService` (o crear uno nuevo)
4. Añadir endpoint de upload en el router correspondiente

### ¿Dónde está la lógica de negocio?
- **Validación de dominio:** En los services (`services/`)
- **Validación de formato:** En los schemas Pydantic (`api/schemas/`)
- **Autenticación:** En `api/dependencies.py` → `get_current_user`
- **Cálculos topográficos:** En `services/calculations/`
- **Parseo de archivos:** En `services/parsers/`

### ¿Cómo encadenar el cálculo de coordenadas aproximadas + MMC?
- **HTTP:** `POST /api/v1/station-setups/{id}/approximate-coordinates` (sin body)
- **Servicio:** `service.calculate_for_station_setup(id)` → `ApproximateCoordinateCalculationResult`
- **Idempotente:** se puede llamar varias veces; borra aproximadas y ajustadas previas y reescribe.
- **Fallo suave:** si el MMC falla (p.ej. matriz N singular), se añade warning y el cálculo de aproximadas sigue.
- **Sin puntos de control:** si todos los visados son referencias, se omite el MMC con warning y no se crean `AdjustedCoordinate`.

---

## 13. COMANDOS ÚTILES

```bash
# Instalar dependencias
uv sync

# Generar SECRET_KEY para .env (si no existe)
openssl rand -base64 32

# Ejecutar servidor de desarrollo
uv run fastapi dev main.py

# Aplicar migraciones
uv run alembic upgrade head

# Crear migración
uv run alembic revision --autogenerate -m "descripción"

# Ejecutar tests
uv run pytest

# Ejecutar tests con output detallado
uv run pytest -v

# Solo tests del MMC
uv run pytest tests/test_least_squares_adjuster.py tests/test_matrix_io.py tests/test_approximate_pipeline.py::TestMMCIntegration tests/test_adjusted_coordinate.py -v

# Tests E2E (importación + cálculo por HTTP real contra oráculos)
uv run pytest tests/test_e2e_c56_excel.py tests/test_e2e_s01_recompute.py -v

# Crear usuario (script independiente)
uv run python create_user.py

# Documentación interactiva
# Abrir http://127.0.0.1:8000/docs
```

---

## 14. NOTAS Y PECULIARIDADES

- **Ángulos en gon (grados centesimales):** Todos los ángulos (hz_angle, v_angle) usan el sistema centesimal (0-400 gon = 0-360°). El proyecto usa constantes como `GON_R = π/200`.
- **Coordenadas con herencia joined-table:** `Coordinate` es la tabla padre, `ApproximateCoordinate`, `AdjustedCoordinate` y `ReferenceCoordinate` son tablas hijas con FK a `coordinates.id`. El borrado bulk de cada hija requiere borrar también la fila padre en `Coordinate` (patrón implementado en los repos correspondientes).
- **Tipos de `circle`:** 1 = directo, 2 = inverso (para el cálculo Bessel).
- **Deduplicación de importaciones:** `UniqueConstraint(project_id, content_hash)` en `ImportSession`. Un mismo archivo PUEDE importarse en distintos proyectos.
- **Fallo suave en Bessel y MMC:** Si un estacionamiento no tiene pares directo/inverso válidos o el MMC falla, se añade warning y el cálculo continúa (no aborta la importación ni el cálculo de aproximadas).
- **StationSetup.matrices (18 columnas LargeBinary):** Almacenan matrices numpy serializadas con `to_bytes` (Etapa 2) como resultado del MMC. Las ajustadas **consultables** son registros `AdjustedCoordinate` (Etapa 3); el blob se mantiene por compatibilidad con el registro crudo del cálculo y no se eliminará.
- **MMC y redundancia:** Con estación fija y un punto observado una vez, `redundancy = num_equations − num_unknowns = 2N − 2N = 0` → sistema compatible determinado. En ese caso `var_post`, `desv_post` y `prec` se fijan a 0 con warning. Las coordenadas ajustadas son válidas, solo las precisiones a posteriori son indefinidas.
- **Script `create_user.py`:** Es independiente de FastAPI. Usa `SessionLocal` directamente y `getpass` para la contraseña.
- **CORS:** Configurado para `localhost:5173` y `localhost:4173` (puertos típicos de Vite dev/preview).
- **`INTER_CONF_DEFAULT`:** Constante global en `least_squares_adjuster.py` con valor `1.9599639845400536` (z al 95 %). Se persiste en `StationSetup.inter_conf_matrix` cada vez que se ejecuta el MMC.

---

## 15. ESTADO DEL PLAN DE AJUSTE MATRICIAL

`docs/PLAN_ajuste_matricial.md` describe la integración del MMC. **Las tres etapas están completadas:**

| Etapa | Descripción | Estado |
|-------|-------------|--------|
| 1 | Modelo de precisiones + calculador puro MMC + tests | **Completada** |
| 2 | `matrix_io.py` — serialización numpy↔bytes | **Completada** |
| 3 | Integración en `approximate_coordinate_service` + persistencia 18 matrices + API REST | **Completada** |

Además, se añadieron los tests **E2E** (`test_e2e_c56_excel.py`, `test_e2e_s01_recompute.py`) que recorren el flujo HTTP completo y verifican cada etapa contra oráculos independientes (Excel y recálculo propio), incluido el álgebra de las matrices MMC persistidas.

Planes detallados:
- `docs/PLAN_etapa1_calculador_mmc.md` — Tareas T1–T7
- `docs/PLAN_etapa2_matrix_io.md` — Etapa 2
- `docs/PLAN_etapa3_integracion_mmc.md` — Tareas T1–T11
