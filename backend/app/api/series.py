from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from backend.app.api.catalog import CatalogRoute
from backend.app.schemas.catalog import ErrorResponse
from backend.app.schemas.series import SeriesResponse
from backend.app.services.catalog import Catalog, get_catalog, products_for_region
from backend.app.services.ds09_series import (
    SITE_IDS,
    DerivedTableError,
    load_ds09_series,
)
from backend.app.services.series import build_series_response, get_snapshot_path
from backend.app.services.series_csv import serialize_series_csv

router = APIRouter(prefix="/api/v1", tags=["series"], route_class=CatalogRoute)


@router.get(
    "/series",
    response_model=SeriesResponse,
    response_model_exclude_defaults=True,
    responses={
        200: {
            "headers": {
                "Cache-Control": {
                    "schema": {"type": "string", "const": "no-store"}
                }
            }
        },
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_series(
    response: Response,
    region_id: Annotated[str, Query(min_length=1)],
    product_id: Annotated[str, Query(min_length=1)],
    start: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")],
    end: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")],
    frequency: Literal["monthly"],
    catalog: Annotated[Catalog, Depends(get_catalog)],
    snapshot_path: Annotated[Path, Depends(get_snapshot_path)],
    site_id: Annotated[str | None, Query(min_length=1)] = None,
) -> SeriesResponse:
    response.headers["Cache-Control"] = "no-store"
    if site_id is not None:
        if site_id not in SITE_IDS:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(404, "RESOURCE_NOT_FOUND", "El sitio solicitado no existe.")
        products = [p for p in products_for_region(catalog, region_id) if p.product_id == product_id]
        if not products:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(404, "RESOURCE_NOT_FOUND", "La región o el producto solicitado no existe.")
        from backend.app.services.series import (
            MAX_SERIES_MONTHS,
            _month_count,
            _parse_month,
        )
        start_date, end_date = _parse_month(start), _parse_month(end)
        if start_date > end_date:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(422, "INVALID_PARAMETER", "El período inicial debe ser anterior o igual al final.")
        expected = _month_count(start_date, end_date)
        if expected > MAX_SERIES_MONTHS:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(422, "LIMIT_EXCEEDED", "La consulta excede el máximo de 240 meses.")
        try:
            return load_ds09_series(catalog=catalog, product=products[0], region_id=region_id, site_id=site_id,
                                    start=start, end=end, expected=expected)
        except DerivedTableError:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(503, "SERVICE_UNAVAILABLE", "La serie derivada DS-09 no está disponible temporalmente.") from None
    return build_series_response(
        catalog, region_id, product_id, start, end, frequency, snapshot_path
    )


@router.get(
    "/series/export.csv",
    response_class=Response,
    responses={
        200: {
            "description": "UTF-8 CSV with monthly observations or one no-data status row.",
            "headers": {
                "Cache-Control": {"schema": {"type": "string", "const": "no-store"}},
                "Content-Disposition": {"schema": {"type": "string"}},
            },
            "content": {
                "text/csv": {
                    "schema": {"type": "string"},
                }
            },
        },
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def export_series_csv(
    region_id: Annotated[str, Query(min_length=1)],
    product_id: Annotated[str, Query(min_length=1)],
    start: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")],
    end: Annotated[str, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")],
    frequency: Literal["monthly"],
    catalog: Annotated[Catalog, Depends(get_catalog)],
    snapshot_path: Annotated[Path, Depends(get_snapshot_path)],
    site_id: Annotated[str | None, Query(min_length=1)] = None,
) -> Response:
    if site_id is not None:
        if site_id not in SITE_IDS:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(404, "RESOURCE_NOT_FOUND", "El sitio solicitado no existe.")
        products = [p for p in products_for_region(catalog, region_id) if p.product_id == product_id]
        if not products:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(404, "RESOURCE_NOT_FOUND", "La región o el producto solicitado no existe.")
        from backend.app.services.series import (
            MAX_SERIES_MONTHS,
            _month_count,
            _parse_month,
        )
        start_date, end_date = _parse_month(start), _parse_month(end)
        if start_date > end_date:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(422, "INVALID_PARAMETER", "El período inicial debe ser anterior o igual al final.")
        try:
            expected = _month_count(start_date, end_date)
            if expected > MAX_SERIES_MONTHS:
                from backend.app.services.series import SeriesRequestError
                raise SeriesRequestError(422, "LIMIT_EXCEEDED", "La consulta excede el máximo de 240 meses.")
            series = load_ds09_series(catalog=catalog, product=products[0], region_id=region_id, site_id=site_id,
                                      start=start, end=end, expected=expected)
        except DerivedTableError:
            from backend.app.services.series import SeriesRequestError
            raise SeriesRequestError(503, "SERVICE_UNAVAILABLE", "La serie derivada DS-09 no está disponible temporalmente.") from None
    else:
        series = build_series_response(
        catalog, region_id, product_id, start, end, frequency, snapshot_path
        )
    return Response(
        content=serialize_series_csv(series),
        media_type="text/csv; charset=utf-8",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'attachment; filename="anomaly-zero-series.csv"',
        },
    )
