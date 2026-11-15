"""Offline tests for FUL-123 planning and CMR identity gates."""

from __future__ import annotations

import json
from typing import Any

import pytest

from backend.app.data_sources.earthdata_probe import DEFAULT_BBOX, PRODUCTS, ProbeError
from research.ful123_acquisition import (
    AcquisitionPlanError,
    _record_matches_plan,
    acquire_months,
    discover_plan,
    eligible_months,
    missing_months,
    verify_resource_budget,
)


def _audit(*, merra: tuple[str, ...] = (), gldas: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "records": [
            {"eligible": True, "product_key": key, "period": month}
            for key, months in (("merra2", merra), ("gldas", gldas))
            for month in months
        ]
    }


class FakeClient:
    """CMR client placeholder; discovery is injected so tests never use network."""


def _granule(product: Any, month: str) -> dict[str, Any]:
    filename = (
        f"MERRA2_300.tavgM_2d_slv_Nx.{month[:4]}{month[5:]}.nc4"
        if product.key == "merra2"
        else f"GLDAS_NOAH025_M.A{month[:4]}{month[5:]}.021.nc4"
    )
    return {
        "granule_id": f"G{int(month[-2:]) + 1_000_000_000}-GES_DISC",
        "producer_granule_id": f"{product.short_name}.{product.version}:{filename}",
        "collection_id": product.expected_collection_id,
        "time_start": f"{month}-01T00:00:00.000Z",
        "time_end": f"{month}-28T23:59:59.000Z",
        "size_mib": 10.0,
    }


def _discoverer(*, status: str = "found", mutate: Any = None):
    def discover(product: Any, month: str, limit: int, bbox: Any, client: Any) -> dict[str, Any]:
        assert client is fake_client
        assert bbox == DEFAULT_BBOX
        assert limit == 2
        rows = [_granule(product, month)] if status == "found" else []
        if mutate:
            rows = mutate(product, month, rows)
        return {"status": status, "granules": rows}

    return discover


fake_client = FakeClient()


def test_eligible_periods_are_taken_only_from_verified_inventory() -> None:
    audit = _audit(merra=("2005-01", "2005-03"), gldas=("2005-01",))

    assert eligible_months(audit, "merra2") == {"2005-01", "2005-03"}
    assert missing_months(audit, "merra2") == [
        "2005-02", "2005-04", "2005-05", "2005-06", "2005-07", "2005-08",
        "2005-09", "2005-10", "2005-11", "2005-12",
    ]
    assert len(missing_months(audit, "gldas")) == 11


def test_plan_reuses_eligible_january_and_discovers_only_missing_months() -> None:
    plan = discover_plan(
        _audit(merra=("2005-01",), gldas=("2005-01",)),
        client=fake_client,
        discoverer=_discoverer(),
    )

    assert len(plan["items"]) == 24
    assert sum(item["status"] == "reused_eligible" for item in plan["items"]) == 2
    assert sum(item["status"] == "discovered" for item in plan["items"]) == 22
    assert plan["transfer_estimate_bytes"] == 22 * 10 * 1024**2
    assert all("?" not in item.get("cmr_metadata_url", "") for item in plan["items"])
    assert all("token" not in str(item).lower() for item in plan["items"])


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda p, m, rows: [{**rows[0], "collection_id": "wrong"}], "cmr_not_found_or_ambiguous"),
        (lambda p, m, rows: [{**rows[0], "producer_granule_id": "wrong:filename"}], "cmr_not_found_or_ambiguous"),
        (lambda p, m, rows: [{**rows[0], "time_start": "2005-03-01"}], "cmr_not_found_or_ambiguous"),
        (lambda p, m, rows: rows * 2, "cmr_not_found_or_ambiguous"),
        (lambda p, m, rows: [{**rows[0], "size_mib": None}], "cmr_size_missing"),
    ],
)
def test_plan_rejects_wrong_ambiguous_or_unpriced_cmr_results(mutate: Any, reason: str) -> None:
    plan = discover_plan(
        _audit(merra=("2005-01",), gldas=("2005-01",)),
        client=fake_client,
        discoverer=_discoverer(mutate=mutate),
    )

    february = next(item for item in plan["items"] if item["product"] == "merra2" and item["month"] == "2005-02")
    assert february["status"] == "blocked"
    assert february["reason"] == reason


def test_plan_records_exact_cmr_identity_and_no_data_or_auth_links() -> None:
    plan = discover_plan(
        _audit(merra=("2005-01",), gldas=("2005-01",)),
        client=fake_client,
        discoverer=_discoverer(),
    )
    merra_feb = next(item for item in plan["items"] if item["product"] == "merra2" and item["month"] == "2005-02")
    gldas_feb = next(item for item in plan["items"] if item["product"] == "gldas" and item["month"] == "2005-02")

    assert merra_feb["collection_id"] == PRODUCTS[0].expected_collection_id
    assert merra_feb["producer_granule_id"].endswith("200502.nc4")
    assert gldas_feb["collection_id"] == PRODUCTS[2].expected_collection_id
    assert gldas_feb["producer_granule_id"].endswith("A200502.021.nc4")
    assert plan["bbox_file_selection_only"] == list(DEFAULT_BBOX)
    assert "authorization" in " ".join(plan["limitations"])
    serialized = str(plan).lower()
    assert ".netrc" not in serialized
    assert "cookie" not in serialized


def test_manifest_must_match_planned_cmr_identity(tmp_path: Any) -> None:
    item = next(
        x for x in _february_pilot_plan()["items"]
        if x["product"] == "merra2" and x["month"] == "2005-02"
    )
    manifest_path = tmp_path / "granule.manifest.json"
    manifest = {
        "granule_id": item["granule_id"],
        "producer_granule_id": item["producer_granule_id"],
        "collection_id": item["collection_id"],
        "period": {"month": item["month"]},
        "product": {"short_name": "M2TMNXSLV", "version": "5.12.4", "variable": "T2M"},
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    record = {"manifest": str(manifest_path)}

    assert _record_matches_plan(record, item)
    manifest["granule_id"] = "G9999999999-GES_DISC"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert not _record_matches_plan(record, item)


def test_resource_budget_boundaries_and_rejection() -> None:
    verify_resource_budget(1_500_000_000, 4 * 1024**3)
    with pytest.raises(AcquisitionPlanError, match="1.5 GiB"):
        verify_resource_budget(2 * 1024**3, 10 * 1024**3)
    with pytest.raises(AcquisitionPlanError, match="4 GiB"):
        verify_resource_budget(1, 4 * 1024**3 - 1)


def _february_pilot_plan() -> dict[str, Any]:
    return discover_plan(
        _audit(merra=("2005-01",), gldas=("2005-01",)),
        client=fake_client,
        discoverer=_discoverer(),
    )


def test_pilot_retries_only_transfer_errors_and_is_resumable_by_granule(
    tmp_path: Any,
) -> None:
    plan = _february_pilot_plan()
    completed: set[tuple[str, str]] = set()
    calls: list[tuple[str, str]] = []
    fail_once: set[tuple[str, str]] = {("merra2", "2005-02")}

    def audit_fn(_: list[Any]) -> dict[str, Any]:
        return {"records": [
            {"product_key": product, "period": month, "eligible": True, "bytes": 123, "sha256": "f" * 64}
            for product, month in completed
        ]}

    def download_fn(item: dict[str, Any], output: Any, strategy: str) -> dict[str, Any]:
        key = (item["product"], item["month"])
        calls.append(key)
        if key in fail_once:
            fail_once.remove(key)
            raise ProbeError("sanitized temporary transfer failure", stage="download")
        completed.add(key)
        return {"status": "downloaded_and_opened"}

    first = acquire_months(
        plan, tmp_path, months={"2005-02"}, max_attempts=3,
        download_fn=download_fn, audit_fn=audit_fn,
        identity_validator=lambda *_: True, sleep_fn=lambda _: None,
    )
    assert calls == [("merra2", "2005-02"), ("merra2", "2005-02"), ("gldas", "2005-02")]
    assert [row["status"] for row in first] == ["payload_verified", "payload_verified"]
    assert first[0]["attempts"] == 2
    progress = tmp_path / ".ful123-acquisition-progress.json"
    assert progress.is_file()
    assert "token" not in progress.read_text(encoding="utf-8").lower()

    second = acquire_months(
        plan, tmp_path, months={"2005-02"}, download_fn=download_fn, audit_fn=audit_fn,
        identity_validator=lambda *_: True,
    )
    assert [row["status"] for row in second] == ["reused_eligible", "reused_eligible"]
    assert len(calls) == 3


def test_later_batch_requires_both_february_pilots_to_be_verified(tmp_path: Any) -> None:
    with pytest.raises(AcquisitionPlanError, match="pilots"):
        acquire_months(
            _february_pilot_plan(), tmp_path, months={"2005-03"},
            download_fn=lambda *_: pytest.fail("must stop before download"),
        )


def test_unverified_existing_file_is_never_overwritten(tmp_path: Any) -> None:
    plan = _february_pilot_plan()
    item = next(x for x in plan["items"] if x["product"] == "merra2" and x["month"] == "2005-02")
    destination = tmp_path / "merra2" / item["producer_granule_id"].split(":")[-1]
    destination.parent.mkdir()
    destination.write_bytes(b"incomplete")

    results = acquire_months(
        plan, tmp_path, months={"2005-02"},
        download_fn=lambda *_: {"status": "downloaded_and_opened"},
        audit_fn=lambda _: {"records": [
            {"product_key": "gldas", "period": "2005-02", "eligible": True,
             "bytes": 200, "sha256": "a" * 64}
        ]},
        identity_validator=lambda *_: True,
    )

    assert results[0]["status"] == "blocked_existing_unverified"
    assert results[1]["status"] == "reused_eligible"
    assert destination.read_bytes() == b"incomplete"


def test_tampered_plan_identity_is_rejected_before_transfer(tmp_path: Any) -> None:
    plan = _february_pilot_plan()
    item = next(x for x in plan["items"] if x["product"] == "merra2" and x["month"] == "2005-02")
    item["producer_granule_id"] = "../../outside.nc4"
    with pytest.raises(AcquisitionPlanError, match="producer identity"):
        acquire_months(
            plan, tmp_path, months={"2005-02"},
            download_fn=lambda *_: pytest.fail("invalid CMR plan must stop before transfer"),
        )


def test_retries_are_bounded_and_authentication_errors_are_not_retried(tmp_path: Any) -> None:
    plan = _february_pilot_plan()
    calls: list[str] = []

    def download_fn(item: dict[str, Any], *_: Any) -> dict[str, Any]:
        calls.append(item["product"])
        raise ProbeError("safe auth failure", stage="authentication")

    results = acquire_months(
        plan, tmp_path, months={"2005-02"}, max_attempts=3,
        download_fn=download_fn, audit_fn=lambda _: {"records": []},
        identity_validator=lambda *_: True,
        sleep_fn=lambda _: pytest.fail("authentication failures must not retry"),
    )

    assert calls == ["merra2", "gldas"]
    assert [result["status"] for result in results] == ["failed", "failed"]
    assert all(result["attempts"] == 1 for result in results)


def test_transfer_retry_stops_after_three_attempts(tmp_path: Any) -> None:
    calls: list[str] = []

    def download_fn(item: dict[str, Any], *_: Any) -> dict[str, Any]:
        calls.append(item["product"])
        raise ProbeError("safe transient failure", stage="download")

    results = acquire_months(
        _february_pilot_plan(), tmp_path, months={"2005-02"}, max_attempts=3,
        download_fn=download_fn, audit_fn=lambda _: {"records": []}, sleep_fn=lambda _: None,
        identity_validator=lambda *_: True,
    )

    assert calls == ["merra2"] * 3 + ["gldas"] * 3
    assert [result["attempts"] for result in results] == [3, 3]
