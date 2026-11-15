from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from backend.app.api.catalog import CatalogRoute
from backend.app.schemas.catalog import ErrorResponse
from backend.app.schemas.series import SeriesResponse
from backend.app.services.catalog import Catalog, get_catalog
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
) -> SeriesResponse:
    response.headers["Cache-Control"] = "no-store"
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
) -> Response:
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
