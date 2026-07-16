"""Camino crítico del parser GKA sobre ficheros reales de docs/."""

from pathlib import Path

from services.parsers.gka_parser import GkaParser

DOCS = Path(__file__).resolve().parent.parent / "docs"


def _parse(filename: str):
    return GkaParser((DOCS / filename).read_text(encoding="utf-8")).parse()


def test_single_station_gka():
    blocks = _parse("20250829_013022_20250829_013939.gka")

    assert len(blocks) == 1
    observations = blocks[0].raw_observations
    assert len(observations) > 0
    # circle ∈ {1, 2}: directo / inverso
    assert all(o.circle in (1, 2) for o in observations)


def test_multi_station_gka():
    blocks = _parse("20251112_200023_20251112_210627.gka")

    assert len(blocks) == 4
    for block in blocks:
        assert block.station.station_name
        assert all(o.circle in (1, 2) for o in block.raw_observations)
