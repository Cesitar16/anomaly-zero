from __future__ import annotations

from copy import deepcopy

import pytest

from research import build_ful116_snapshot as snapshot
from research.ful117_contract import (
    ROOT,
    assert_local_references_resolve,
    assert_scientific_semantics,
    iter_openapi_examples,
    load_spec,
    markdown_json_examples,
    validate_schema,
)
from research.tests.test_ful116_snapshot import _write_granules


def _series_payload(**overrides):
    payload = {
        "contract_version": "0.1-draft",
        "synthetic": True,
        "generated_at": "2026-01-01T00:00:00Z",
        "data_state": "available_with_gaps",
        "product": {
            "short_name": "GPM_3IMERGM",
            "variable": "precipitation",
            "unit": "mm/hr",
            "quantity": "monthly_mean_rate",
        },
        "series": [
            {"date": "2005-01-01", "value": 0.0, "quality": {"state": "unassessed", "missing_reason": None}},
            {"date": "2005-02-01", "value": None, "quality": {"state": "missing", "missing_reason": "provider_fill_value"}},
        ],
        "spatial_aggregation": {"support_type": "point_sample", "approval_state": "not_assessed"},
        "coverage": {"spatial_coverage": None},
        "quality": {"verification_state": "basic_checks_only", "provider_flags_applied": False, "qa_checks": []},
        "transformations": [],
    }
    payload.update(overrides)
    return payload


def test_all_openapi_response_examples_validate_and_are_explicitly_synthetic():
    spec = load_spec()
    ref_count = assert_local_references_resolve(spec)
    examples = list(iter_openapi_examples(spec))

    assert ref_count >= 80
    assert len(examples) >= 10
    for path, method, status, media, name, schema, value in examples:
        errors = validate_schema(schema, value, spec)
        assert not errors, f"{method} {path} {status} {name}: {errors}"
        assert value["synthetic"] is True, f"{method} {path} {status} {name} fixture is not marked synthetic"
        assert_scientific_semantics(value)


def test_openapi_rejects_non_string_product_version():
    spec = load_spec()
    example = next(
        item
        for item in iter_openapi_examples(spec)
        if item[0] == "/series" and "product" in item[-1]
    )
    invalid = deepcopy(example[-1])
    invalid["product"]["product_version"] = 7
    errors = validate_schema(example[-2], invalid, spec)
    assert errors


def test_markdown_json_fixtures_validate_against_matching_openapi_schema():
    spec = load_spec()
    examples = markdown_json_examples(ROOT / "docs/contracts-v0.md")
    assert len(examples) >= 6
    for example in examples:
        if "error" in example:
            name = "ErrorResponse"
        elif "analysis_id" in example:
            name = "AnalysisResponse"
        else:
            name = "SeriesResponse"
        errors = validate_schema({"$ref": f"#/components/schemas/{name}"}, example, spec)
        assert not errors, f"{name}: {errors}"
        assert_scientific_semantics(example)


def test_ful116_snapshot_points_conform_to_series_point_schema(tmp_path, monkeypatch):
    input_dir, point_path = _write_granules(tmp_path, monkeypatch)
    result = snapshot.build_snapshot(input_dir, point_path, tmp_path / "processed")
    spec = load_spec()

    assert result["synthetic"] is True
    assert result["spatial_aggregation"]["support_type"] == "point_sample"
    assert result["quality"]["verification_state"] == "basic_checks_only"
    assert result["quality"]["provider_flags_applied"] is False
    for point in result["series"]:
        errors = validate_schema({"$ref": "#/components/schemas/SeriesPoint"}, point, spec)
        assert not errors, errors


def test_scientific_semantics_accept_zero_null_and_fill_reason():
    assert_scientific_semantics(_series_payload())


@pytest.mark.parametrize(
    "payload,match",
    [
        (_series_payload(product={"short_name": "GPM_3IMERGM", "variable": "precipitation", "unit": "mm/hr", "quantity": "monthly_accumulation"}), "acumulado"),
        (_series_payload(contract_version="0.2-draft"), "contract_version incompatible"),
        (_series_payload(product={"short_name": "GPM_3IMERGM", "variable": "precipitation", "unit": "mm", "quantity": "monthly_mean_rate"}), "Variable/unidad incoherentes"),
        (_series_payload(quality={"verification_state": "provider_qa_applied", "provider_flags_applied": True, "qa_checks": []}), "evidenciados"),
        (_series_payload(spatial_aggregation={"support_type": "regional_aggregate", "approval_state": "approved"}), "referencia verificable"),
        (_series_payload(spatial_aggregation={"support_type": "regional_aggregate", "approval_state": "approved", "approval_reference": "synthetic-test-only"}), "No existe una referencia documental"),
        (
            _series_payload(
                coverage={"spatial_coverage": {"valid_area_fraction_of_basin": 1.000046}},
                spatial_aggregation={
                    "support_type": "regional_aggregate",
                    "approval_state": "approved",
                    "approval_reference": "synthetic-test-only",
                },
            ),
            "bloquea agregación",
        ),
        (_series_payload(series=[{"date": "2005-01-01", "value": None, "quality": {"state": "missing", "missing_reason": None}}]), "requiere missing_reason"),
        (_series_payload(series=[{"date": "2005-01-15", "value": 1.0, "quality": {"state": "unassessed", "missing_reason": None}}]), "primer día del mes"),
        (_series_payload(series=[{"date": "2005-13-01", "value": 1.0, "quality": {"state": "unassessed", "missing_reason": None}}]), "Fecha mensual inválida"),
        (_series_payload(generated_at="2026-13-40T00:00:00Z"), "fecha válida"),
        (_series_payload(synthetic=True), "no puede usarse como observación real"),
    ],
)
def test_scientific_semantics_rejects_false_or_unsupported_claims(payload, match):
    with pytest.raises(ValueError, match=match):
        assert_scientific_semantics(payload, production=match == "no puede usarse como observación real")


def test_gate_t_does_not_allow_production_complete_or_pending_metrics():
    complete = {
        "contract_version": "0.1-draft",
        "synthetic": False,
        "generated_at": "2026-01-01T00:00:00Z",
        "analysis_id": "analysis-real-001",
        "status": "complete",
    }
    with pytest.raises(ValueError, match="Gate T"):
        assert_scientific_semantics(complete, production=True)

    pending = {
        **complete,
        "status": "pending",
        "metrics": {"p_value": 0.02},
    }
    with pytest.raises(ValueError, match="métricas calculadas"):
        assert_scientific_semantics(pending, production=True)

