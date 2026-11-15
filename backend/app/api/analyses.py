from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import Path as PathParameter

from backend.app.api.catalog import CatalogRoute
from backend.app.schemas.analysis import CreateAnalysisRequest
from backend.app.schemas.catalog import ErrorResponse
from backend.app.services.analysis import validate_analysis_request
from backend.app.services.catalog import Catalog, get_catalog
from backend.app.services.series import SeriesRequestError, get_snapshot_path

router = APIRouter(prefix="/api/v1", tags=["analyses"], route_class=CatalogRoute)


@router.post(
    "/analyses",
    status_code=409,
    responses={
        409: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def create_analysis(
    request: CreateAnalysisRequest,
    catalog: Annotated[Catalog, Depends(get_catalog)],
    snapshot_path: Annotated[Path, Depends(get_snapshot_path)],
) -> None:
    validate_analysis_request(request, catalog, snapshot_path)


@router.get(
    "/analyses/{analysis_id}",
    status_code=404,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_analysis(
    analysis_id: Annotated[str, PathParameter(min_length=1)],
) -> None:
    raise SeriesRequestError(
        404, "RESOURCE_NOT_FOUND", "El análisis solicitado no existe."
    )
