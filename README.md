# TopoData Backend

API RESTful en Python (FastAPI) para la gestión, almacenamiento y procesamiento de datos topográficos. El sistema estructura la información jerárquicamente: proyectos → sesiones de importación → estacionamientos → observaciones brutas → observaciones Bessel → coordenadas.

---

## 🚀 Tecnologías Principales

| Categoría | Tecnología |
|-----------|-----------|
| **Framework** | FastAPI (≥ 0.133) |
| **Lenguaje** | Python ≥ 3.14 |
| **Gestor de dependencias** | `uv` |
| **Base de datos** | SQLite (fichero local en `sqlite_database/dev.db`) |
| **Migraciones** | Alembic |
| **ORM** | SQLAlchemy 2.0+ (estilo `Mapped`) |
| **Validación** | Pydantic v2 |
| **Autenticación** | JWT (pyjwt) + bcrypt |
| **Cálculos topográficos** | pandas + numpy |
| **Proyecciones** | pyproj (derivación de parámetros de elipsoide desde EPSG) |
| **Tiempo GPS** | gps-time |
| **Tests** | pytest + httpx |

---

## 📁 Estructura del Proyecto

```
topodata_backend/
├── main.py                       # Punto de entrada FastAPI (lifespan, CORS, routers)
├── create_user.py                # Script CLI independiente para crear usuarios
├── pyproject.toml                # Dependencias (uv), ruff, pytest
├── alembic.ini                   # Configuración de Alembic
├── .env                          # Variables de entorno (SECRET_KEY, etc.) — ¡obligatorio!
│
├── core/
│   └── config.py                 # Settings (pydantic-settings): JWT secret, algoritmo, expiración
│
├── data/
│   ├── database/
│   │   ├── engine.py             # Engine SQLAlchemy, SessionLocal, get_db, SessionDep
│   │   └── models/               # Modelos ORM (SQLAlchemy Mapped + DeclarativeBase)
│   │       ├── base.py           #   Base
│   │       ├── project.py        #   Project (parámetros elipsoidales, constantes)
│   │       ├── import_session.py #   ImportSession (UniqueConstraint project+hash)
│   │       ├── station_setup.py  #   StationSetup (matrices binarias LargeBinary)
│   │       ├── raw_observation.py#   RawObservation (ángulos en gon, circle 1/2)
│   │       ├── bessel_observation.py # BesselObservation (12 columnas: dir+inv+bessel+delta)
│   │       ├── coordinate.py     #   Coordinate (polimórfica joined-table, discriminator "type")
│   │       ├── approximate_coordinate.py # ApproximateCoordinate (FK→bessel_observations)
│   │       ├── adjusted_coordinate.py    #   AdjustedCoordinate (FK→bessel_observations) [MMC]
│   │       ├── reference_coordinate.py   # ReferenceCoordinate (FK→projects)
│   │       └── user.py           #   User (bcrypt hash, is_active, is_superuser)
│   └── repositories/             # Patrón Repository (BaseRepository[T] genérico)
│       ├── base_repository.py    #   get, get_all, count, create, update, delete, refresh
│       ├── project_repository.py
│       ├── import_session_repository.py  # get_by_project, get_by_project_and_hash
│       ├── station_setup_repository.py   # get_by_import_session
│       ├── raw_observation_repository.py # get_by_station_setup, delete_by_station_setup (bulk)
│       ├── bessel_observation_repository.py
│       ├── approximate_coordinate_repository.py # get_by_bessel_observation, delete_by_station_setup
│       ├── adjusted_coordinate_repository.py    # get_by_bessel_observation, delete_by_station_setup [MMC]
│       ├── reference_coordinate_repository.py   # get_by_project
│       └── user_repository.py            # get_by_username, get_by_email, exists_by_*
│
├── api/
│   ├── dependencies.py           # TODAS las factorías de DI (repos, services, auth)
│   ├── routes/                   # Routers FastAPI (prefijo /api/v1/...)
│   │   ├── project_router.py     #   CRUD proyectos + POST import_gka/{id}
│   │   ├── import_session_router.py
│   │   ├── station_setup_router.py
│   │   ├── raw_observation_router.py
│   │   ├── bessel_observation_router.py
│   │   ├── reference_coordinate_router.py
│   │   ├── approximate_coordinate_router.py
│   │   ├── adjusted_coordinate_router.py  #   [MMC] Solo lectura: /api/v1/adjusted-coordinates
│   │   └── user_router.py        #   /auth/register, /auth/login, /auth/me, /users
│   └── schemas/                  # Schemas Pydantic v2 (Base/Create/Update/Response/Parsed)
│       ├── project_schemas.py    #   ProjectBase con @model_validator para derivar elipsoide
│       ├── import_session_schemas.py
│       ├── station_setup_schemas.py
│       ├── raw_observaton_schemas.py  # Nota: typo histórico en el nombre de archivo
│       ├── bessel_observation_schemas.py
│       ├── coordinate_schemas.py #   CoordinateBase polimórfico
│       ├── approximate_coordinate_schemas.py
│       ├── adjusted_coordinate_schemas.py #   [MMC] AdjustedCoordinateBase/Create/Response
│       ├── reference_coordinate_schemas.py
│       ├── user_schemas.py       #   UserCreate/Update/Response + LoginRequest + TokenResponse
│       └── parser_schemas.py     #   GkaImportResult
│
├── services/
│   ├── project_service.py        # CRUD proyectos + cascada de borrado manual
│   ├── import_session_service.py # CRUD sesiones + validación hash único
│   ├── import_orchestrator_service.py # Orquestador de importación GKA → DB
│   ├── station_setup_service.py  # CRUD estacionamientos + borrado en cascada de hijos
│   ├── raw_observation_service.py
│   ├── bessel_observation_service.py  # CRUD + cálculo Bessel automático (idempotente)
│   ├── approximate_coordinate_service.py # CRUD + pipeline completo (Cassini → MMC)
│   ├── adjusted_coordinate_service.py    # [MMC] Solo lectura de coordenadas ajustadas
│   ├── reference_coordinate_service.py
│   ├── user_service.py           # register, login (JWT), CRUD usuarios
│   ├── password_service.py       # bcrypt hash/verify
│   ├── token_service.py          # JWT encode/decode
│   ├── parsers/
│   │   ├── parser_base.py        # ABC: file_content + lines (lazy) + parse() abstracto
│   │   ├── gka_parser.py         # Parser de archivos .gka (formato Leica GNV11)
│   │   └── utils/
│   │       └── parsers_utils.py  # get_str, get_req_str, get_float, get_int, ...
│   └── calculations/
│       ├── bessel_adjuster.py    # Cálculo de promedios Bessel (pandas pivot_table + numpy)
│       ├── station_position_calculator.py # Inversa planimétrica, k_utm, cota estación (ZEST)
│       ├── approximate_coordinate_calculator.py # Desorientación + radiación de coordenadas
│       ├── least_squares_adjuster.py   # [MMC] Ajuste por mínimos cuadrados (numpy)
│       └── matrix_io.py               # [MMC] Serialización numpy↔bytes (18 matrices)
│
├── tests/
│   ├── conftest.py               # Fixtures: DB SQLite en memoria, client, auth_client
│   ├── test_auth.py              # Endpoints protegidos (401/200)
│   ├── test_gka_parser.py        # Parser GKA con ficheros reales
│   ├── test_bessel_adjuster.py   # Corrección numérica BesselAdjuster
│   ├── test_import_orchestrator.py # Orquestador: import OK + dedup por proyecto
│   ├── test_approximate_coordinate.py
│   ├── test_approximate_pipeline.py
│   ├── test_station_position.py
│   ├── test_least_squares_adjuster.py # [MMC] Tests unitarios del ajuste
│   ├── test_matrix_io.py          # [MMC] Round-trip numpy↔bytes
│   ├── test_adjusted_coordinate.py # [MMC] Tests HTTP de endpoints ajustados
│   ├── test_e2e_c56_excel.py      # E2E: levantamiento C56 vs Excel
│   ├── test_e2e_s01_recompute.py  # E2E: levantamiento S01 por recálculo
│   ├── e2e_helpers.py             # Driver HTTP + oráculos de recálculo (no test)
│   └── bessel_tests.py            # Test manual Bessel contra DB real (no pytest)
│
├── alembic/
│   ├── env.py                    # target_metadata = Base.metadata
│   └── versions/                 # Historial de migraciones
│
├── docs/
│   ├── LLM-REFERENCE.md          # Referencia completa para agentes LLM
│   ├── ajustes_topografia.py     # Implementación independiente del Colab (oráculo de tests)
│   ├── *.gka                     # Ficheros .gka de ejemplo para tests (C56, S01, etc.)
│   ├── matrices/                 # Excel de especificación del MMC
│   ├── Cálculo coord aproximadas.xlsx / Cálculo desorientación.xlsx / Cálculo de Z del estacionamiento.xlsx
│   ├── Pasos de cálculo v1.pdf   # Procedimiento de cálculo de referencia
│   └── PLAN_*.md                 # Planes del ajuste matricial (etapas 1-3)
│
└── sqlite_database/              # Directorio de la BD SQLite (dev.db)
```

---

## 🔐 Autenticación

La API usa **OAuth2 Password Bearer** con tokens JWT:

1. **Registrar un usuario:** `POST /api/v1/auth/register`
2. **Iniciar sesión:** `POST /api/v1/auth/login` → devuelve `{access_token, token_type: "bearer"}`
3. **Usar el token:** Incluir `Authorization: Bearer <token>` en todas las peticiones

Todos los endpoints excepto `/auth/register` y `/auth/login` requieren autenticación.
El token expira según `ACCESS_TOKEN_EXPIRE_MINUTES` (por defecto 120 min).

---

## 🛠️ Instalación y Configuración

### 1. Requisitos previos

- Python ≥ 3.14
- `uv` (gestor de dependencias): https://docs.astral.sh/uv/

### 2. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd topodata_backend
uv sync
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con al menos:

```env
SECRET_KEY="una-clave-secreta-aleatoria-de-al-menos-32-caracteres"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

> ⚠️ **Importante:** La aplicación no arranca sin `SECRET_KEY`. Usa `openssl rand -base64 32` para generar una clave segura.

### 4. Crear la base de datos y aplicar migraciones

```bash
uv run alembic upgrade head
```

Esto crea `sqlite_database/dev.db` con todas las tablas.

### 5. Crear el primer usuario

```bash
uv run python create_user.py
```

El script te pedirá nombre de usuario, email, contraseña y si es superusuario de forma interactiva.

### 6. Ejecutar el servidor

```bash
uv run fastapi dev main.py
```

- API: `http://127.0.0.1:8000`
- Documentación Swagger: `http://127.0.0.1:8000/docs`
- CORS habilitado para `localhost:5173` y `localhost:4173` (puertos de Vite)

---

## 📡 Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Registrar nuevo usuario |
| `POST` | `/api/v1/auth/login` | Iniciar sesión (obtener JWT) |
| `GET` | `/api/v1/auth/me` | Obtener usuario autenticado |
| `GET` | `/api/v1/users` | Listar todos los usuarios |
| `GET` | `/api/v1/users/{id}` | Obtener un usuario |
| `PATCH` | `/api/v1/users/{id}` | Actualizar usuario (parcial) |
| `DELETE` | `/api/v1/users/{id}` | Eliminar usuario |
| `GET` | `/api/v1/projects` | Listar proyectos |
| `GET` | `/api/v1/projects/count` | Contar proyectos |
| `GET` | `/api/v1/projects/{id}` | Obtener proyecto |
| `GET` | `/api/v1/projects/{id}/name` | Obtener solo el nombre del proyecto |
| `POST` | `/api/v1/projects` | Crear proyecto |
| `PUT` | `/api/v1/projects/{id}` | Actualizar proyecto |
| `DELETE` | `/api/v1/projects/{id}` | Eliminar proyecto (cascada manual) |
| `POST` | `/api/v1/projects/import_gka/{id}` | Importar archivo .gka (multipart) |
| `GET` | `/api/v1/import-sessions` | Listar sesiones (filtro: `?project_id=`) |
| `GET` | `/api/v1/station-setups` | Listar estacionamientos (filtro: `?import_session_id=`) |
| `POST` | `/api/v1/station-setups/{id}/approximate-coordinates` | Dispara el pipeline completo (Cassini → k_utm → ZEST → desorientación → radiación → MMC) |
| `GET` | `/api/v1/raw-observations` | Listar observaciones brutas (filtro: `?station_setup_id=`) |
| `GET` | `/api/v1/bessel-observations` | Listar observaciones Bessel (filtro: `?station_setup_id=`) |
| `GET` | `/api/v1/reference-coordinates` | Listar coordenadas de referencia (filtro: `?project_id=`) |
| `GET` | `/api/v1/approximate-coordinates` | Listar coordenadas aproximadas |
| `GET` | `/api/v1/approximate-coordinates/by-station-setup/{id}` | Coordenadas aproximadas de un estacionamiento |
| `GET` | `/api/v1/adjusted-coordinates` | Listar coordenadas ajustadas por MMC |
| `GET` | `/api/v1/adjusted-coordinates/by-station-setup/{id}` | Coordenadas ajustadas de un estacionamiento |

> Todos los endpoints tienen `POST`, `PUT`, `DELETE` y `/count` además de `GET`. Consulta `/docs` para el esquema completo.

---

## 🔄 Flujo de Importación GKA (el flujo principal)

```
POST /api/v1/projects/import_gka/{project_id}   (multipart .gka)
    │
    ▼
ImportOrchestratorService.process_gka_import()
    │
    ├─1. GkaParser.parse()                     → extrae bloques #GNV11..#END11
    ├─2. SHA-256 del contenido                  → deduplicación por proyecto
    ├─3. Crea ImportSession                     (UniqueConstraint project+hash)
    ├─4. Para cada estacionamiento parseado:
    │     ├─ Crea StationSetup
    │     ├─ Crea RawObservation (una por cada línea parseada)
    │     └─ BesselObservationService.calculate_for_station_setup()
    │          └─ BesselAdjuster: pivotea por target_name + circle (1=directo, 2=inverso)
    │             y calcula promedios Bessel. Si no hay pares válidos → warning, no aborta.
    └─5. Retorna GkaImportResult (import_session + station_setups + raw_observations + warnings)
```

---

## 🔄 Pipeline de Coordenadas Aproximadas + MMC

Disparado por `POST /api/v1/station-setups/{id}/approximate-coordinates` (sin body). Es **idempotente** (borra y reescribe aproximadas y ajustadas previas) y de **fallo suave** (si el MMC falla, añade warning y sigue con las aproximadas).

```
1. Cargar entidades (station_setup, import_session, project, bessel, raw, refs)
   └─ ValueError si falta alguna o hay < 3 referencias

2. Resección Cassini → (etr_x, etr_y)
3. k_utm = factor de escala UTM
4. ZEST → etr_z (cota de la estación)
5. Desorientación (ε) del estacionamiento
6. Radiación → coordenadas aproximadas por cada observación Bessel

7. MMC (mínimos cuadrados) sobre los puntos de control (no referencias):
   ├─ LeastSquaresAdjuster (A, Aᵀ, P, N=AᵀPA, N⁻¹, x, v, precisiones)
   ├─ Persiste 18 matrices numpy en StationSetup (columnas LargeBinary)
   └─ Crea un AdjustedCoordinate por punto de control (x, y, z, prec_x, prec_y)

8. Recrea ApproximateCoordinate preservando prec_senal / prec_punteria_cc
9. Devuelve ApproximateCoordinateCalculationResult (aproximadas + ajustadas + warnings)
```

---

## 🧪 Tests

```bash
# Ejecutar todos los tests (86 actualmente)
uv run pytest

# Ejecutar tests específicos
uv run pytest tests/test_gka_parser.py -v

# Solo tests del MMC
uv run pytest tests/test_least_squares_adjuster.py tests/test_matrix_io.py tests/test_adjusted_coordinate.py -v

# Tests E2E (importación + cálculo por HTTP real contra oráculos)
uv run pytest tests/test_e2e_c56_excel.py tests/test_e2e_s01_recompute.py -v
```

Los tests usan **SQLite en memoria** (no tocan `dev.db`). Las fixtures en `conftest.py` proporcionan:
- `client`: `TestClient` con DB aislada
- `auth_client`: `client` con token JWT (usuario `tester` / `supersecret`)
- `db_session`: sesión SQLAlchemy directa para tests de servicio

Los tests **E2E** (`test_e2e_c56_excel.py` y `test_e2e_s01_recompute.py`) recorren el flujo HTTP real (proyecto → referencias → importación GKA → cálculo) y verifican cada etapa contra **oráculos independientes**: los Excel de referencia (levantamiento C56) y un recálculo independiente de la lógica del Colab (`docs/ajustes_topografia.py` + helpers en `tests/e2e_helpers.py`).

---

## 🏗️ Arquitectura y Principios de Diseño

```
┌─────────────────────────────────────────────┐
│  API (routes + schemas)                     │  ← Presentación
├─────────────────────────────────────────────┤
│  api/dependencies.py                        │  ← Inyección de Dependencias
├─────────────────────────────────────────────┤
│  services/*                                 │  ← Lógica de negocio
├─────────────────────────────────────────────┤
│  data/repositories/*                        │  ← Acceso a datos (patrón Repository)
├─────────────────────────────────────────────┤
│  data/database/models/*                     │  ← Modelos ORM
└─────────────────────────────────────────────┘
```

**Principios clave:**
- **Inyección de dependencias:** Los routers NUNCA instancian servicios/repositorios directamente. Usan tipos `Annotated` definidos en `api/dependencies.py` (ej: `ProjectServiceDep`, `ImportSessionRepositoryDep`).
- **Cascada de borrado manual:** NO se usa `cascade` de SQLAlchemy. El borrado en cascada es explícito en los services (ej: `ProjectService.delete_project` → `ImportSessionService.delete_import_session` → `StationSetupService._delete_station_setup_children` → bulk delete de observaciones y coordenadas).
- **Validación en schemas:** `ProjectBase.populate_geodetic_parametrs` usa `pyproj` para derivar `a_elip`, `b_elip`, `f_elip`, `inv_f_elip` desde el código EPSG.
- **Fallo suave en Bessel:** Si un estacionamiento no tiene pares directo/inverso válidos, el cálculo Bessel se omite (warning) pero la importación NO aborta.
- **Deduplicación de importaciones:** `UniqueConstraint(project_id, content_hash)` en `ImportSession`. El mismo archivo PUEDE importarse en distintos proyectos.
- **Ángulos en gon:** Todos los ángulos usan el sistema centesimal (0-400 gon). El proyecto usa constantes como `GON_R = π/200`.
- **Coordenadas con herencia joined-table:** `Coordinate` es la tabla padre; `ApproximateCoordinate`, `AdjustedCoordinate` y `ReferenceCoordinate` son tablas hijas. El borrado bulk de cada hija debe borrar también la fila padre en `Coordinate`.
- **MMC (mínimos cuadrados):** `LeastSquaresAdjuster` calcula la cadena `A → Aᵀ → P → N=AᵀPA → N⁻¹ → x → v` para los puntos de control. Los 18 resultados se serializan con `matrix_io` y se persisten en `StationSetup` como `LargeBinary`, y se crea un `AdjustedCoordinate` consultable por cada control.

---

## 📋 Jerarquía de Entidades y Cascada de Borrado

```
Project
 └─ ImportSession          ← UniqueConstraint(project_id, content_hash)
      └─ StationSetup      ← matrices binarias LargeBinary (MMC)
           ├─ RawObservation
           ├─ BesselObservation
           ├─ ApproximateCoordinate → Coordinate (joined-table)
           └─ AdjustedCoordinate → Coordinate (joined-table) [MMC]
ReferenceCoordinate → Coordinate (independiente, cuelga de Project)
```

El borrado es **siempre manual y explícito** de arriba hacia abajo.

---

## 📚 Documentación Adicional

- **`docs/LLM-REFERENCE.md`**: Referencia exhaustiva para agentes LLM con catálogo completo de clases, funciones, flujos y patrones.
- **`docs/ajustes_topografia.py`**: Implementación independiente de la lógica del Colab (oráculo para validar resultados en los tests E2E).
- **`docs/PLAN_ajuste_matricial.md`**: Plan general del ajuste por mínimos cuadrados (MMC) — etapas 1-3 completadas.
- **`docs/matrices/` + Excel de cálculo**: Especificación del MMC y valores de referencia para verificar los resultados.
- **`http://127.0.0.1:8000/docs`**: Documentación interactiva Swagger UI auto-generada.

---

## 🔧 Comandos Útiles

```bash
uv sync                          # Instalar dependencias
uv run fastapi dev main.py       # Servidor de desarrollo con hot-reload
uv run alembic upgrade head      # Aplicar migraciones pendientes
uv run alembic revision --autogenerate -m "descripción"  # Crear nueva migración
uv run pytest                    # Ejecutar tests
uv run pytest -v                 # Ejecutar tests con output detallado
uv run pytest tests/test_e2e_c56_excel.py tests/test_e2e_s01_recompute.py -v  # Tests E2E
uv run python create_user.py     # Crear usuario interactivo
```
