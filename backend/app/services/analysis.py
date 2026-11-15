from pathlib import Path
from typing import Any

from backend.app.schemas.analysis import CreateAnalysisRequest
from backend.app.services.catalog import Catalog
from backend.app.services.series import (
    MAX_SERIES_MONTHS,
    SeriesRequestError,
    _month_count,
    _parse_month,
    read_optional_snapshot,
)


def validate_analysis_request(
    request: CreateAnalysisRequest,
    catalog: Catalog,
    snapshot_path: Path,
) -> None:
    """Validate current dataset/window availability; no analysis is executed."""
    start, end = _parse_month(request.window.start), _parse_month(request.window.end)
    if start > end:
        raise SeriesRequestError(
            422,
            "INVALID_PARAMETER",
            "El período inicial debe ser anterior o igual al final.",
        )
    if _month_count(start, end) > MAX_SERIES_MONTHS:
        raise SeriesRequestError(
            422, "LIMIT_EXCEEDED", "La consulta excede el máximo de 240 meses."
        )

    snapshot = read_optional_snapshot(snapshot_path)
    if snapshot is None or request.dataset_id != snapshot["dataset_id"]:
        raise SeriesRequestError(
            404, "RESOURCE_NOT_FOUND", "El dataset solicitado no existe."
        )

    product = next(
        (
            item
            for item in catalog.products
            if item.short_name == snapshot["product"]["short_name"]
        ),
        None,
    )
    region = next(
        (item for item in catalog.regions if item.region_id == "murray-darling-basin"),
        None,
    )
    if product is None or region is None:
        raise SeriesRequestError(
            404, "RESOURCE_NOT_FOUND", "El dataset solicitado no existe."
        )

    coverage = snapshot["available_coverage"]
    if (
        request.window.start < coverage["start"]
        or request.window.end > coverage["end"]
    ):
        raise SeriesRequestError(
            422,
            "PERIOD_OUT_OF_COVERAGE",
            "El período solicitado excede la cobertura publicada.",
        )

    metrics: dict[str, Any] = {
        "slope": None,
        "slope_unit": None,
        "confidence_interval": None,
        "p_value": None,
        "significance": None,
    }
    raise SeriesRequestError(
        409,
        "ANALYSIS_METHOD_UNAVAILABLE",
        "No hay un método estadístico aprobado y habilitado; no se creó un análisis.",
        details={
            "analysis": {
                "state": "not_available",
                "analysis_id": None,
                "dataset_id": request.dataset_id,
                "region_id": region.region_id,
                "product_id": product.product_id,
                "window": request.window.model_dump(),
                "method": None,
                "metrics": metrics,
            }
        },
    )
