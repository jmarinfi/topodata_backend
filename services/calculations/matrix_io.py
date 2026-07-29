import io

import numpy as np


def to_bytes(arr) -> bytes:
    """Serializa un ndarray (o array-like) a bytes (.npy).

    Preserva dtype y shape en la cabecera nativa de numpy, sin metadatos
    externos. Acepta cualquier iterable convertible via ``np.asarray``.
    """
    buf = io.BytesIO()
    np.save(buf, np.asarray(arr))
    return buf.getvalue()


def from_bytes(b: bytes) -> np.ndarray:
    """Deserializa bytes (.npy) a ndarray.

    ``allow_pickle=False`` por seguridad: no se ejecuta codigo arbitrario.
    """
    return np.load(io.BytesIO(b), allow_pickle=False)


def scalar_to_bytes(x) -> bytes:
    """Serializa un escalar (int/float) a bytes como array 0-d."""
    return to_bytes(np.asarray(x))


def scalar_from_bytes(b: bytes):
    """Deserializa bytes a escalar Python nativo.

    ``.item()`` devuelve el tipo nativo (un ``int`` sigue siendo ``int``,
    un ``float`` sigue siendo ``float``).
    """
    return from_bytes(b).item()
