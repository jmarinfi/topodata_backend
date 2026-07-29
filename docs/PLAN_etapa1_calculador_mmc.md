# Plan — Etapa 1: Calculador puro MMC + modelo de precisiones

> Derivado de `docs/PLAN_ajuste_matricial.md` (cierra su **Supuesto 1**) a partir del
> procedimiento de `docs/matrices/Cálculo parámetros v2.xlsx`.
> **Alcance:** modelo + migración + calculador puro + tests unitarios.
> Quedan fuera (etapas posteriores): integración en `approximate_coordinate_service`,
> helper de serialización `matrix_io.py` y exposición por API.

## Contexto

`docs/PLAN_ajuste_matricial.md` define un ajuste por mínimos cuadrados (MMC) que refina las
coordenadas aproximadas radiadas. Su **Supuesto 1** quedó abierto: no se sabía si la matriz P
usaba una fórmula simple o el modelo rico del Excel.

El nuevo `docs/matrices/Cálculo parámetros v2.xlsx` **resuelve ese supuesto**: P usa un modelo de
precisiones **a priori por observación** (σ angular y σ de distancia totales). Esto exige **4
campos nuevos** en el modelo de datos y cambia la construcción de P en el calculador.

El calculador es puro (numpy, sin DB), instanciado y validable contra los oráculos del Excel.

---

## Fórmulas verificadas contra los Excel (oráculos)

**Precisiones a priori** (`Cálculo parámetros v2.xlsx`, columnas M y N, fila 10):

```
σ_angular_cc (M) = sqrt( (prec_ang_etr · s_sexa_cc)²                              # teodolito
                       + (prec_senal / dist_utm · r_cc)²                           # error de señal/prisma
                       + prec_punteria_cc² )                                       # puntería
σ_dist_m    (N) = sqrt( prec_senal²                                                # señal (m)
                      + (prec_dist_mm/1000 + prec_dist_ppm·1e-6 · dist_utm)² )     # distanciómetro (mm+ppm)
```

**Pesos de P** (`Generación matriz P.xlsx`, filas 15–24): `P` diagonal con
`peso_dirección = 1/σ_angular_cc²` y `peso_distancia = 1/σ_dist_m²`.

**Matriz A** (`Generación matriz A v3.xlsx`, fila 15), por observación `i`:
- ΔE = `approx_x − station_x`; ΔN = `approx_y − station_y`; `dist_calc = hypot(ΔE, ΔN)`
- Fila dirección: `[dx_i = ΔN·R_CC/dist_calc², dy_i = −ΔE·R_CC/dist_calc²]`
- Fila distancia: `[dx_i = ΔE/dist_utm,    dy_i = ΔN/dist_utm]`

**Matriz L** (`Generación matriz L.xlsx`):
- Dirección: `−(acim_calc − acim_obs)·10000`  (con `acim_calc = atan2(ΔE,ΔN)/GON_R` normalizado a [0,400))
- Distancia: `−(dist_calc − dist_utm)`

**Cadena** (`Cálculos entre matrices.xlsx`):
`tra_a=Aᵀ; tra_a_p=AᵀP; n=AᵀPA; inver_n=n⁻¹; t=AᵀPL; x=inver_n·t; v=Ax−L; tra_v_p=vᵀP`
`num_eq=filas(A); num_unk=cols(A); red=num_eq−num_unk; var_post=(vᵀPv)/red; desv_post=√var_post`

**Salidas**: `prec_i = desv_post · inter_conf · √(inver_n[i,i])`; `coord_ajustada_i = coord_aprox_i + x_i`.
`inter_conf = 1.9599639845400536` (z al 95 %, `Cálculos entre matrices.xlsx!B23`).

**Constantes** (G3–G7 del Excel == clase `Project`): `GON_R=π/200`, `EARTH_RADIUS=6378000`,
`S_SEXA_CC=250/81`, `R_CC=2000000/π`. ✓

**Orden de filas**: N filas de dirección seguidas de N filas de distancia (confirmado en A y P).
Columnas: `dx_1,dy_1,…,dx_k,dy_k` (una pareja por punto **único**; observaciones repetidas del
mismo `target_name` mapean a la misma pareja de columnas → generan redundancia).

**Fuera de alcance**: columnas Q (dist. cuerda = `dist_utm/k_utm`) y R (σAH) del Excel de
parámetros — **no** las consumen ni P ni la matriz de precisiones. Se ignoran (auxiliares).

---

## Decisiones fijadas con el usuario

| Campo | Default | Modelo | Motivo |
|---|---|---|---|
| `prec_senal` | `0.0` (m) | **`ApproximateCoordinate`** | depende del prisma/diana → por punto visado |
| `prec_punteria_cc` | `3.09` (cc) | **`ApproximateCoordinate`** | depende del prisma/diana → por punto visado |
| `prec_dist_mm` | `0.8` (mm) | **`ImportSession`** | depende de la estación total → común a toda la sesión |
| `prec_dist_ppm` | `1` (ppm) | **`ImportSession`** | depende de la estación total → común a toda la sesión |

- `prec_ang_etr` (0.5″) y `kt_coef_refr` (0.13) ya existen en `ImportSession` (se reutilizan).
- `inter_conf` sigue siendo **constante** en el calculador (sin campo de modelo).

---

## Tareas (pequeñas y específicas)

### T1 — Modelo `ImportSession` (`data/database/models/import_session.py`)
Añadir junto a `prec_ang_etr` (líneas 24–25), mismo patrón (`Float`, default + server_default):
```python
prec_dist_mm: Mapped[float] = mapped_column(Float, default=0.8)
prec_dist_ppm: Mapped[float] = mapped_column(Float, default=1)
```
> En la migración (T3) llevar `server_default="0.8"` / `"1"` para rellenar filas existentes en `dev.db`.

### T2 — Modelo `ApproximateCoordinate` (`data/database/models/approximate_coordinate.py`)
Añadir dos columnas a la tabla hija `approximate_coordinates` (herencia joined-table):
```python
prec_senal: Mapped[float] = mapped_column(Float, default=0.0)
prec_punteria_cc: Mapped[float] = mapped_column(Float, default=3.09)
```
> Los registros existentes de coordenadas aproximadas tomarán los defaults; la creación actual
> en `approximate_coordinate_service` no necesita cambios (el default aplica).

### T3 — Migración Alembic
`uv run alembic revision --autogenerate -m "precisions mmc: distanciómetro en ImportSession y señal/puntería en ApproximateCoordinate"`.
Revisar que añade 2 columnas a `import_sessions` y 2 a `approximate_coordinates` con
`server_default` (`0.8`, `1`, `0.0`, `3.09`). `uv run alembic upgrade head`.

### T4 — Schemas Pydantic (exponer los 4 campos con defaults)
- `api/schemas/import_session_schemas.py`: `prec_dist_mm`, `prec_dist_ppm` en `ImportSessionBase` (defaults 0.8 / 1) → heredan Create/Update/Response.
- `api/schemas/approximate_coordinate_schemas.py`: `prec_senal`, `prec_punteria_cc` en `ApproximateCoordinateBase` (defaults 0.0 / 3.09) → heredan Create/Update/Response.
> Siguen el patrón existente; `from_attributes=True` ya está en los Response.

### T5 — Calculador puro `services/calculations/least_squares_adjuster.py`
Patrón de `station_position_calculator.py` / `bessel_adjuster.py`: clase instanciada, sin DB/repos,
numpy para álgebra lineal (`np.linalg.inv`, `@`), lanza `ValueError`.

**Constante**: `INTER_CONF_DEFAULT = 1.9599639845400536`.

**`@dataclass LsTarget`** (desacopla de `RadiacionResult`; lleva `prec_senal`/`prec_punteria` por punto):
```python
target_name: str
approx_x: float          # = RadiacionResult.x
approx_y: float          # = RadiacionResult.y
dist_utm: float          # = RadiacionResult.dist_utm
acimut_observado: float  # = RadiacionResult.acimut (gon, [0,400))
prec_senal: float        # por punto (default 0.0)
prec_punteria_cc: float  # por punto (default 3.09)
```

**Constructor**:
```python
LeastSquaresAdjuster(station_x, station_y, targets: list[LsTarget],
                     gon_r, r_cc, s_sexa_cc, prec_ang_etr, prec_dist_mm, prec_dist_ppm,
                     inter_conf: float = INTER_CONF_DEFAULT)
```

**`calculate() -> LeastSquaresResult`**:
1. Mapeo `target_name → índice de columna` (primer orden de aparición; repeticiones = misma incógnita).
2. Por observación `i`: ΔE/ΔN/dist_calc/acim_calc; **σ_dir_i** y **σ_dist_i** (fórmulas M/N).
3. Construir `A` (2N_eq × 2N_unk), `L` (2N_eq,), `P` diagonal (2N_eq × 2N_eq).
4. Cadena: `tra_a, tra_a_p, n, inver_n=np.linalg.inv(n)`, `t, x=inver_n@t, v=a@x-l, tra_v_p`.
5. Escalares: `num_equations, num_unknowns, redundancy, var_post, desv_post`.
6. Si `redundancy ≤ 0`: `var_post=desv_post=0.0`, `prec` a ceros, añadir `warning` (precisiones no definidas; sistema compatible determinado). Aun así calcular `x` y `adjusted_coords`.
7. Si `n` es singular (`np.linalg.LinAlgError`) o no hay observaciones → `raise ValueError` (mensaje en español).
8. `prec_i = desv_post · inter_conf · np.sqrt(np.diag(inver_n))`; `adjusted_coords = [(name, approx_x+x[2k], approx_y+x[2k+1)]`.

**`@dataclass LeastSquaresResult`**: arrays `sigma_dir, sigma_dist, a, tra_a, p, tra_a_p, l, n,
inver_n, t, x, v, tra_v_p`; escalares `num_equations, num_unknowns, redundancy, var_post,
desv_post, inter_conf`; `prec` (array 2k); `adjusted_coords: list[tuple[str,float,float]]`;
`warnings: list[str]`. (Se exponen `sigma_dir/sigma_dist` para validar contra M/N.)

### T6 — Tests `tests/test_least_squares_adjuster.py`
Construir `LsTarget` con los datos del Excel. Casos:
- **(a) Oráculos de precisión**: con `prec_ang_etr=0.5, s_sexa_cc=250/81, prec_punteria=3.09,
  prec_senal=0, mm=0.8, ppm=1` → `sigma_dir[0] ≈ 3.4539248288` (M10) y, para `dist_utm=87.39099…`,
  `sigma_dist[0] ≈ 8.87391e-4` (N10); para `dist_utm=133.26547…`, `sigma_dist ≈ 9.33265e-4` (N11).
- **(b) Coeficientes de A**: para ΔE=−127.4318, ΔN=38.99909, dist_calc=133.26589 → `A[dir,dx] ≈ 1397.97`,
  `A[dir,dy] ≈ 4567.94` (celdas C15/D15 del Excel A).
- **(c) Pesos de P**: `P[dir,dir] ≈ 1/3.45392² ≈ 0.083825`; `P[dist,dist] ≈ 1/8.87391e-4²`.
- **(d) Identidades algebraicas**: `n ≈ aᵀ@p@a`; `x ≈ inver_n@t`; `v ≈ a@x−l`; `vᵀPv ≥ 0` y coherente.
- **(e) Redundancia 0** (4 puntos distintos, 1 observación c/u): `redundancy==0`, `desv_post==0`,
  `prec` todo ceros, y `warnings` no vacío; `adjusted_coords` no nulo.
- **(f) Redundancia 2** (ejemplo P1–P4 con P2 observado dos veces, como los Excel A/P): `redundancy==2`,
  `desv_post>0`, `prec>0`.
- **(g) Errores**: sin observaciones → `ValueError`.

### T7 — Documentación
Actualizar `docs/PLAN_ajuste_matricial.md`: cerrar el **Supuesto 1** (modelo rico confirmado),
reflejar los 4 campos nuevos y su ubicación, y marcar que la Etapa 1 añade modelo (modifica el
punto "4. Sin cambios de modelo" → ahora sí hay migración en esta etapa).

---

## Ficheros

**Nuevos:** `services/calculations/least_squares_adjuster.py`, `tests/test_least_squares_adjuster.py`, migración Alembic.
**Modificados:** `import_session.py`, `approximate_coordinate.py`, sus schemas (`import_session_schemas.py`, `approximate_coordinate_schemas.py`), `docs/PLAN_ajuste_matricial.md`.

---

## Verificación (Etapa 1)

1. `uv run alembic upgrade head` — migración aplica sin error y `dev.db` queda con las 4 columnas.
2. `uv run pytest tests/test_least_squares_adjuster.py -v` — pasan (a)–(g).
3. `uv run pytest -v` — sin regresiones (Bessel, parser, orchestrator, auth).
4. Sanity: importar que `LeastSquaresAdjuster` no importa nada de `data/` ni `api/` (pureza).

**Fuera de esta etapa** (etapas siguientes): `matrix_io.py`, encadenado en
`approximate_coordinate_service.calculate_for_station_setup`, persistencia de las 18 matrices y
exposición por API.
