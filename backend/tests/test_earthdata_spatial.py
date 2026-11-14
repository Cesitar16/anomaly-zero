from __future__ import annotations

import pytest

from backend.app.data_sources import earthdata_probe as probe
from backend.app.data_sources.earthdata_spatial import (
    _geometries,
    _inside,
    _ring_classify,
)


def _ring(x0: float, y0: float, x1: float, y1: float) -> list[list[float]]:
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]


def _parse_polygon(
    exterior: list[list[float]], holes: list[list[list[float]]] | None = None
) -> list[tuple[list, list[list]]]:
    geometry = {"type": "Polygon", "coordinates": [exterior, *(holes or [])]}
    return list(_geometries(geometry))


def test_ring_classification_distinguishes_inside_outside_and_boundary() -> None:
    ring = _ring(0, 0, 10, 10)

    assert _ring_classify(5, 5, ring) == "inside"
    assert _ring_classify(0, 5, ring) == "boundary"
    assert _ring_classify(11, 5, ring) == "outside"


def test_polygon_without_holes_covers_inside_and_excludes_outside() -> None:
    polygons = _parse_polygon(_ring(0, 0, 10, 10))

    assert _inside(5, 5, polygons) is True
    assert _inside(11, 5, polygons) is False


@pytest.mark.parametrize("point", [(0, 5), (0, 0), (5, 10)])
def test_polygon_covers_exterior_edges_and_vertices(point: tuple[float, float]) -> None:
    polygons = _parse_polygon(_ring(0, 0, 10, 10))

    assert _inside(*point, polygons) is True


def test_polygon_with_multiple_holes_excludes_only_strict_hole_interiors() -> None:
    polygons = _parse_polygon(
        _ring(0, 0, 12, 12),
        [_ring(2, 2, 4, 4), _ring(7, 7, 10, 10)],
    )

    assert _inside(3, 3, polygons) is False
    assert _inside(8, 8, polygons) is False
    assert _inside(6, 6, polygons) is True


@pytest.mark.parametrize("point", [(2, 3), (2, 2)])
def test_polygon_covers_hole_edges_and_vertices(point: tuple[float, float]) -> None:
    polygons = _parse_polygon(_ring(0, 0, 10, 10), [_ring(2, 2, 6, 6)])

    assert _inside(*point, polygons) is True


def test_multipolygon_classifies_components_independently() -> None:
    geometry = {
        "type": "MultiPolygon",
        "coordinates": [[_ring(0, 0, 2, 2)], [_ring(5, 5, 7, 7)]],
    }
    polygons = list(_geometries(geometry))

    assert _inside(1, 1, polygons) is True
    assert _inside(6, 6, polygons) is True
    assert _inside(2, 1, polygons) is True  # boundary of first component
    assert _inside(3, 3, polygons) is False


@pytest.mark.parametrize(
    "ring",
    [
        [[0, 0], [1, 0], [1, 1], [0, 1]],  # not closed
        [[0, 0], [1, 0], [0, 0]],  # too few positions
        [[0, 0], [1, 0], [1, float("nan")], [0, 0]],  # non-finite
    ],
)
def test_polygon_rejects_malformed_rings(ring: list[list[float]]) -> None:
    with pytest.raises(probe.ProbeError, match="ring"):
        _parse_polygon(ring)
