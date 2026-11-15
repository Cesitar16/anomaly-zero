"""Versioned, offline catalog metadata. No region geometry is approved yet."""

from dataclasses import dataclass

from backend.app.schemas.catalog import Product, Region


class CatalogNotFound(Exception):
    """The requested region is not in the published region catalog."""


class CatalogUnavailable(Exception):
    """The local catalog cannot be read."""


@dataclass(frozen=True)
class Catalog:
    regions: tuple[Region, ...]
    products: tuple[Product, ...]
    synthetic: bool = False


PRODUCTS = (
    Product(
        product_id="P01",
        short_name="M2TMNXSLV",
        product_version="5.12.4",
        variable="T2M",
        quantity="air_temperature_2m",
        unit="K",
        availability="unavailable",
        source={
            "agency": "NASA GMAO",
            "distributor": "GES DISC",
            "collection_id": "C1276812859-GES_DISC",
            "doi": "10.5067/AP1B0BA5PD2K",
            "source_urls": ["https://doi.org/10.5067/AP1B0BA5PD2K"],
            "granule_ids": [],
        },
        current_dataset_id=None,
        coverage=None,
        quality=None,
    ),
    Product(
        product_id="P02",
        short_name="GPM_3IMERGM",
        product_version="07",
        variable="precipitation",
        quantity="monthly_mean_rate",
        unit="mm/hr",
        availability="unavailable",
        source={
            "agency": "NASA/JAXA",
            "distributor": "GES DISC",
            "collection_id": "C2723754851-GES_DISC",
            "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
            "source_urls": [
                "https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07"
            ],
            "granule_ids": [],
        },
        current_dataset_id=None,
        coverage=None,
        quality=None,
    ),
    Product(
        product_id="P03",
        short_name="GLDAS_NOAH025_M",
        product_version="2.1",
        variable="SoilMoi0_10cm_inst",
        quantity="soil_moisture_layer_0_10_cm",
        unit="kg m-2",
        availability="unavailable",
        source={
            "agency": "NASA GSFC",
            "distributor": "GES DISC",
            "collection_id": "C1342986036-GES_DISC",
            "doi": "10.5067/SXAVCZFAQLNO",
            "source_urls": ["https://doi.org/10.5067/SXAVCZFAQLNO"],
            "granule_ids": [],
        },
        current_dataset_id=None,
        coverage=None,
        quality=None,
    ),
)

# No region is exposed until its geometry and provenance are approved.
CATALOG = Catalog(regions=(), products=PRODUCTS)


def get_catalog() -> Catalog:
    return CATALOG


def products_for_region(catalog: Catalog, region_id: str) -> list[Product]:
    if not any(region.region_id == region_id for region in catalog.regions):
        raise CatalogNotFound(region_id)
    return list(catalog.products)
