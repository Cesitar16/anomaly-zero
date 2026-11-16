import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from backend.app.schemas.catalog import (
    ErrorResponse,
    MonthRange,
    ProductsResponse,
    RegionsResponse,
)
from backend.app.schemas.context_geometry import ContextualGeometryFeatureCollection
from backend.app.services.catalog import (
    Catalog,
    CatalogNotFound,
    CatalogUnavailable,
    get_catalog,
    products_for_region,
)
from backend.app.services.context_geometry import (
    CONTEXT_REGION_ID,
    ContextGeometryUnavailableError,
    get_context_geometry_path,
    read_context_geometry,
)
from backend.app.services.ds09_series import SITE_IDS, TABLE_PRODUCT, table_available
from backend.app.services.series import (
    SeriesRequestError,
    get_snapshot_path,
    product_for_snapshot,
    read_optional_snapshot,
)
from backend.app.services.snapshot_reader import SnapshotUnavailableError

logger = logging.getLogger(__name__)


class GeoJSONResponse(JSONResponse):
    media_type = "application/geo+json"


def _error_response(
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
    details: dict | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        contract_version="0.1-draft",
        synthetic=False,
        generated_at=datetime.now(UTC),
        error={
            "code": code,
            "message": message,
            "retryable": retryable,
            "request_id": str(uuid4()),
            "details": details,
        },
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
        headers={"Cache-Control": "no-store"},
    )


async def catalog_not_found(_: Request, exc: CatalogNotFound) -> JSONResponse:
    return _error_response(404, "RESOURCE_NOT_FOUND", "La región solicitada no existe.")


async def catalog_unavailable(_: Request, exc: CatalogUnavailable) -> JSONResponse:
    return _error_response(
        503,
        "SERVICE_UNAVAILABLE",
        "El catálogo no está disponible temporalmente.",
        retryable=True,
    )


async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(422, "INVALID_PARAMETER", "Los parámetros de la petición no son válidos.")


async def internal_error(_: Request, exc: Exception) -> JSONResponse:
    return _error_response(500, "INTERNAL_ERROR", "Ocurrió un error interno.")


class CatalogRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as exc:
                return await invalid_request(request, exc)
            except CatalogNotFound as exc:
                return await catalog_not_found(request, exc)
            except CatalogUnavailable as exc:
                return await catalog_unavailable(request, exc)
            except ContextGeometryUnavailableError:
                return _error_response(
                    503,
                    "SERVICE_UNAVAILABLE",
                    "El contorno contextual no está disponible temporalmente.",
                    retryable=True,
                )
            except SnapshotUnavailableError:
                return _error_response(
                    503,
                    "SERVICE_UNAVAILABLE",
                    "El snapshot de datos no está disponible temporalmente.",
                    retryable=True,
                )
            except SeriesRequestError as exc:
                return _error_response(
                    exc.status_code, exc.code, exc.public_message, details=exc.details
                )
            except Exception as exc:  # noqa: BLE001 - sanitize unexpected catalog faults.
                logger.exception("Unexpected catalog request failure")
                return await internal_error(request, exc)

        return handle


router = APIRouter(prefix="/api/v1", tags=["catalog"], route_class=CatalogRoute)


@router.get(
    "/regions/{region_id}/geometry",
    operation_id="getContextRegionGeometry",
    response_class=Response,
    response_model=ContextualGeometryFeatureCollection,
    responses={
        200: {
            "description": "GeoJSON contextual; no es una máscara científica aprobada.",
            "content": {
                "application/geo+json": {
                    "schema": {
                        "$ref": "#/components/schemas/ContextualGeometryFeatureCollection"
                    }
                }
            },
            "headers": {
                "Cache-Control": {"schema": {"type": "string", "const": "no-store"}}
            },
        },
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_region_geometry(
    region_id: str,
    catalog: Annotated[Catalog, Depends(get_catalog)],
) -> Response:
    if region_id != CONTEXT_REGION_ID or not any(
        region.region_id == region_id for region in catalog.regions
    ):
        raise CatalogNotFound(region_id)
    payload = read_context_geometry(get_context_geometry_path())
    return GeoJSONResponse(
        content=payload,
        headers={"Cache-Control": "no-store"},
    )


@router.get(
    "/regions",
    response_model=RegionsResponse,
    responses={
        200: {
            "headers": {
                "Cache-Control": {
                    "schema": {"type": "string", "const": "no-store"}
                }
            }
        },
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def list_regions(
    response: Response,
    catalog: Annotated[Catalog, Depends(get_catalog)],
) -> RegionsResponse:
    response.headers["Cache-Control"] = "no-store"
    return RegionsResponse(
        contract_version="0.1-draft",
        synthetic=catalog.synthetic,
        generated_at=datetime.now(UTC),
        regions=list(catalog.regions),
    )


@router.get(
    "/products",
    response_model=ProductsResponse,
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
def list_products(
    response: Response,
    region_id: Annotated[str, Query(min_length=1)],
    catalog: Annotated[Catalog, Depends(get_catalog)],
    snapshot_path: Annotated[Path, Depends(get_snapshot_path)],
) -> ProductsResponse:
    response.headers["Cache-Control"] = "no-store"
    snapshot = read_optional_snapshot(snapshot_path)
    products = products_for_region(catalog, region_id)
    products = [
        product.model_copy(update={
            "availability": "available",
            "product_version": TABLE_PRODUCT[product.product_id][2],
            "current_dataset_id": f"ds09-{product.product_id.lower()}-candidate-sites-2005",
            "coverage": MonthRange(start="2005-01", end="2005-12"),
            "quality": {
                "source_flag_fields": [], "provider_flags_applied": False,
                "source_missing_attributes": {"fill_value": None, "missing_value": None, "scale_factor": None, "add_offset": None},
                "finite_non_fill_filter_applied": False, "verification_state": "unassessed",
                "mask_applied": None, "qa_checks": [], "uninterpreted_provider_fields": [],
            },
        }) if not catalog.synthetic and region_id == "murray-darling-basin" and any(table_available(product.product_id, site) for site in SITE_IDS) else product
        for product in products
    ]
    if snapshot is not None:
        products = [
            product_for_snapshot(product, snapshot)
            if product.short_name == snapshot["product"]["short_name"]
            else product
            for product in products
        ]
    return ProductsResponse(
        contract_version="0.1-draft",
        synthetic=catalog.synthetic or bool(snapshot and snapshot["synthetic"]),
        generated_at=datetime.now(UTC),
        region_id=region_id,
        products=products,
    )
