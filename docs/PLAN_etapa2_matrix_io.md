# Plan — Etapa 2: Helper de serialización numpy↔bytes (`matrix_io.py`)

## Contexto

La Etapa 1 dejó listo el calculador puro `LeastSquaresAdjuster`, que devuelve un
`LeastSquaresResult` con matrices/vectores numpy y escalares. La Etapa 3 (integración) deberá
persistir esos resultados en las **18 columnas `LargeBinary`** de `StationSetup`
([station_setup.py:34-57](../data/database/models/station_setup.py#L34-L57)).

Actualmente **no existe ningún (de)serializador numpy↔bytes** en el repo (confirmado: ni
`np.save`/`np.load`, ni `tobytes`/`frombuffer`, ni `pickle`). Esta etapa introduce **una vez** ese
helper, genérico y sin acoplamiento a DB/repos, para que la Etapa 3 sólo tenga que llamarlo al
extender el `update(...)` del servicio.

**Objetivo:** utilidad pura que serializa cualquier `np.ndarray` (y escalares) a `bytes`
auto-descriptivos y los reconoce sin pérdida (dtype + shape + valores).

---

## Diseño

Formato **`.npy` nativo** de numpy (vía `np.save`/`np.load`): es autodescriptivo (preserva
dtype y shape en la propia cabecera), sin metadatos externos y **sin `pickle`**
(`np.load` se usa con `allow_pickle=False` → no hay riesgo de ejecución arbitraria; nunca
serializamos arrays de objetos).

Funciones en `services/calculations/matrix_io.py`:

```python
import io
import numpy as np

def to_bytes(arr) -> bytes:
    """Serializa un ndarray (o array-like) a bytes (.npy). Preserva dtype y shape."""
    buf = io.BytesIO()
    np.save(buf, np.asarray(arr))
    return buf.getvalue()

def from_bytes(b: bytes) -> np.ndarray:
    """Deserializa bytes (.npy) a ndarray. allow_pickle=False por seguridad."""
    return np.load(io.BytesIO(b), allow_pickle=False)

def scalar_to_bytes(x) -> bytes:
    """Serializa un escalar (int/float) a bytes (array 0-d)."""
    return to_bytes(np.asarray(x))

def scalar_from_bytes(b: bytes):
    """Deserializa bytes a escalar Python nativo (.item(): int sigue int, float sigue float)."""
    return from_bytes(b).item()
```

**Decisiones:**
- `to_bytes`/`from_bytes` son **genéricas** (cualquier ndarray: 2D, 1D, 0-d, structured). No
  especializan ningún campo.
- `scalar_to_bytes`/`scalar_from_bytes` son *wrappers* finos por claridad e intención del
  llamador. `scalar_from_bytes` usa `.item()` para devolver el tipo nativo (un `int` como
  `num_equations` no se convierte a `float`).
- **`None` no se trata aquí**: las columnas son `nullable`, pero la gestión de `None` (columna
  no calculada) corresponde a la Etapa 3. El helper es estricto bytes↔array.

### Mapeo de las 18 columnas (referencia para Etapa 3)
- **Arrays** (`to_bytes`/`from_bytes`): `v, a, tra_a, p, tra_a_p, x, l, n, inver_n, t, tra_v_p, prec` (12).
- **Escalares** (`scalar_to_bytes`/`scalar_from_bytes`): `desv_post` (float), `var_post` (float),
  `num_equations` (int), `num_unknowns` (int), `inter_conf` (float) (5).
- **`adjust_coord`** (lista `(str, float, float)`): **fuera de esta etapa**. Mezcla texto+número;
  su representación (p. ej. Nx2 floats guardando solo x/y, o structured-array con campo unicode
  `U`, o reasociar nombres por orden de columna) se decide al integrar (Etapa 3).

---

## Tareas (pequeñas y específicas)

### T1 — Helper `services/calculations/matrix_io.py`
Crear el módulo con las 4 funciones anteriores. Sin imports de `data/` ni `api/` (utilidad pura).
Docstrings en español. `allow_pickle=False` explícito en `np.load` (defensa en profundidad).

### T2 — Tests `tests/test_matrix_io.py`
Casos (sin redundancia entre ellos):
- **(a) Round-trip matriz 2D float**: `from_bytes(to_bytes(M))` conserva **shape, dtype y
  valores** (`np.allclose` + `.shape` + `.dtype`).
- **(b) Round-trip vector 1D**.
- **(c) dtype preservado en enteros**: un array `int` vuelve como `int` (no `float`).
- **(d) Round-trip array vacío** (`np.array([])`): no falla y conserva shape `(0,)`.
- **(e) `to_bytes` devuelve `bytes`** (`isinstance(..., bytes)`).
- **(f) Escalar float**: `scalar_from_bytes(scalar_to_bytes(3.14)) == 3.14`.
- **(g) Escalar int**: `scalar_from_bytes(scalar_to_bytes(8)) == 8` y `isinstance(..., int)`.
- **(h) Keystone end-to-end**: construir un `LeastSquaresResult` real vía `LeastSquaresAdjuster`
  (reutilizar fixture de `tests/test_least_squares_adjuster.py` — 2 puntos), serializar los **12
  arrays + 5 escalares** con la función que corresponda, deserializar y afirmar igualdad
  (`np.allclose` arrays, `==` escalares). Valida el mapeo exacto que usará la Etapa 3.

### T3 — Documentación
Anotar en `docs/PLAN_ajuste_matricial.md` (sección del helper) que `matrix_io.py` queda
implementado y que `adjust_coord` queda pendiente para la Etapa 3.

---

## Ficheros

**Nuevos:** `services/calculations/matrix_io.py`, `tests/test_matrix_io.py`.
**Modificados (solo doc):** `docs/PLAN_ajuste_matricial.md`.

---

## Verificación (Etapa 2)

1. `uv run pytest tests/test_matrix_io.py -v` — pasan (a)–(h).
2. `uv run pytest -v` — sin regresiones (Etapa 1 incluida).
3. Sanity: `matrix_io.py` no importa nada de `data/` ni `api/` (pureza).

**Fuera de esta etapa:** encadenado en
`approximate_coordinate_service.calculate_for_station_setup`, persistencia efectiva de las 18
columnas, representación de `adjust_coord` y exposición por API (todo Etapa 3).
