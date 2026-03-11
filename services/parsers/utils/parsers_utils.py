def get_str(columns: list[str], idx: int) -> str | None:
    if idx < len(columns):
        val = columns[idx].strip()
        return val if val else None
    return None


def get_req_str(columns: list[str], idx: int) -> str:
    val = get_str(columns, idx)
    if val is not None:
        return val
    raise ValueError(f"Falta un string obligatorio en la columna {idx}")


def get_float(columns: list[str], idx: int) -> float | None:
    val = get_str(columns, idx)
    return float(val) if val is not None else None


def get_req_float(columns: list[str], idx: int) -> float:
    val = get_float(columns, idx)
    if val is not None:
        return val
    raise ValueError(f"Falta un float obligatorio en la columna {idx}")


def get_int(columns: list[str], idx: int) -> int | None:
    val = get_str(columns, idx)
    return int(val) if val is not None else None


def get_req_int(columns: list[str], idx: int) -> int:
    val = get_int(columns, idx)
    if val is not None:
        return val
    raise ValueError(f"Falta un int obligatorio en la columna {idx}")
