from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from backend.app.schemas.catalog import (
    ErrorResponse,
    ProductsResponse,
    RegionsResponse,
)
from backend.app.services.catalog import (
    Catalog,
    CatalogNotFound,
    CatalogUnavailable,
    get_catalog,
    products_for_region,
)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
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
            "details": None,
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
            except Exception as exc:  # noqa: BLE001 - sanitize unexpected catalog faults.
                return await internal_error(request, exc)

        return handle


router = APIRouter(prefix="/api/v1", tags=["catalog"], route_class=CatalogRoute)


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
) -> ProductsResponse:
    response.headers["Cache-Control"] = "no-store"
    return ProductsResponse(
        contract_version="0.1-draft",
        synthetic=catalog.synthetic,
        generated_at=datetime.now(UTC),
        region_id=region_id,
        products=products_for_region(catalog, region_id),
    )
