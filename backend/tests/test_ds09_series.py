from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.ds09_series import SITE_IDS, TABLE_PRODUCT

client = TestClient(app)


def test_ds09_endpoint_publishes_each_authentic_derived_series_with_its_own_cell():
    responses = []
    for product_id in TABLE_PRODUCT:
        for site_id in SITE_IDS:
            response = client.get("/api/v1/series", params={
                "region_id": "murray-darling-basin", "product_id": product_id,
                "site_id": site_id, "start": "2005-01", "end": "2005-12",
                "frequency": "monthly",
            })
            assert response.status_code == 200, f"{product_id}/{site_id}: {response.text}"
            body = response.json()
            assert body["synthetic"] is False
            assert body["data_state"] == "available"
            assert len(body["series"]) == 12
            assert body["product"]["unit"] == TABLE_PRODUCT[product_id][4]
            assert body["spatial_aggregation"]["support_type"] == "point_sample"
            assert body["spatial_aggregation"]["approval_state"] == "not_assessed"
            assert "not reverified" in body["provenance"]["manifest_version"]
            assert "no implica" in body["message"]
            responses.append(body)
    assert len({item["spatial_aggregation"]["point"]["cell_id"] for item in responses}) == 9


def test_unknown_ds09_site_is_not_silently_replaced():
    response = client.get("/api/v1/series", params={
        "region_id": "murray-darling-basin", "product_id": "P01", "site_id": "basin_center",
        "start": "2005-01", "end": "2005-12", "frequency": "monthly",
    })
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
