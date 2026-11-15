from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path

import h5py
import pytest

from backend.app.services.snapshot_reader import (
    MAX_SNAPSHOT_BYTES,
    SnapshotInvalidError,
    SnapshotUnavailableError,
    read_snapshot,
)
from research import build_ful116_snapshot as snapshot_builder
from research.ful117_contract import load_spec, validate_schema
from research.snapshot_format import canonical_json, snapshot_sha256
from research.tests.test_ful116_snapshot import _write_granules


@pytest.fixture
def synthetic_snapshot(tmp_path, monkeypatch):
    input_dir, point_file = _write_granules(tmp_path / "inputs", monkeypatch)
    output_dir = tmp_path / "processed"
    result = snapshot_builder.build_snapshot(input_dir, point_file, output_dir)
    return output_dir / "imerg_2005_point_snapshot.json", result, input_dir


def _write_snapshot(path: Path, payload: dict, *, refresh_hash: bool = True) -> None:
    value = deepcopy(payload)
    if refresh_hash:
        value["snapshot_sha256"] = snapshot_sha256(value)
    path.write_bytes(canonical_json(value) + b"\n")


def test_reads_valid_synthetic_snapshot_without_changing_inputs(synthetic_snapshot):
    path, generated, input_dir = synthetic_snapshot
    before = {file.name: snapshot_builder.sha256_file(file) for file in input_dir.iterdir()}
    snapshot_bytes = path.read_bytes()

    result = read_snapshot(path)

    assert result == generated
    assert result["synthetic"] is True
    assert result["spatial_aggregation"]["support_type"] == "point_sample"
    assert result["product"]["unit"] == "mm/hr"
    assert result["series"][0]["value"] == 0.0
    assert result["series"][1]["value"] is None
    assert result["series"][1]["quality"]["missing_reason"] == "provider_fill_value"
    assert path.read_bytes() == snapshot_bytes
    assert {file.name: snapshot_builder.sha256_file(file) for file in input_dir.iterdir()} == before


def test_reader_does_not_run_pipeline_open_hdf5_or_access_network(synthetic_snapshot, monkeypatch):
    path, _, _ = synthetic_snapshot

    def forbidden(*args, **kwargs):
        pytest.fail("snapshot reader attempted generation, HDF5 access, or network access")

    monkeypatch.setattr(snapshot_builder, "build_snapshot", forbidden)
    monkeypatch.setattr(h5py, "File", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)

    assert read_snapshot(path)["synthetic"] is True


def test_rejects_invalid_hash_and_json(synthetic_snapshot, tmp_path):
    _path, payload, _ = synthetic_snapshot
    tampered = deepcopy(payload)
    tampered["limitations"][0] = "tampered content"
    tampered_path = tmp_path / "tampered.json"
    _write_snapshot(tampered_path, tampered, refresh_hash=False)
    with pytest.raises(SnapshotInvalidError, match="hash"):
        read_snapshot(tampered_path)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{", encoding="utf-8")
    with pytest.raises(SnapshotInvalidError, match="JSON"):
        read_snapshot(invalid_json)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda data: data.pop("dataset_id"), "dataset identity"),
        (lambda data: data.update(dataset_id="imerg-2005-point-00000000000000000000"), "identity does not match"),
        (lambda data: data.update(snapshot_schema_version="9.0.0"), "version"),
        (lambda data: data["series"].__setitem__(1, data["series"][0]), "periods"),
        (lambda data: data["coverage"].update(valid_periods=12), "coverage"),
        (lambda data: data["product"].update(unit="mm"), "product identity"),
        (lambda data: data["spatial_aggregation"].update(support_type="regional_aggregate"), "spatial support"),
        (lambda data: data["provenance"]["source_records"][0].update(sha256="invalid"), "hashes"),
    ],
)
def test_rejects_inconsistent_snapshot_fields(synthetic_snapshot, tmp_path, mutation, message):
    _, generated, _ = synthetic_snapshot
    path = tmp_path / "mutated.json"
    altered = deepcopy(generated)
    mutation(altered)
    _write_snapshot(path, altered)

    with pytest.raises(SnapshotInvalidError, match=message):
        read_snapshot(path)


def test_rejects_missing_fields_and_incompatible_identity(synthetic_snapshot, tmp_path):
    _, generated, _ = synthetic_snapshot
    for name, mutation in (
        ("missing-coverage", lambda value: value.pop("coverage")),
        ("bad-variable", lambda value: value["product"].update(variable="temperature")),
    ):
        path = tmp_path / f"{name}.json"
        changed = deepcopy(generated)
        mutation(changed)
        _write_snapshot(path, changed)
        with pytest.raises(SnapshotInvalidError):
            read_snapshot(path)


def test_rejects_json_nan_and_infinity(synthetic_snapshot, tmp_path):
    _, generated, _ = synthetic_snapshot
    changed = deepcopy(generated)
    changed["series"][0]["value"] = float("inf")
    path = tmp_path / "infinity.json"
    path.write_text(json.dumps(changed, allow_nan=True), encoding="utf-8")

    with pytest.raises(SnapshotInvalidError, match="non-finite"):
        read_snapshot(path)


def test_distinguishes_missing_inaccessible_and_oversized_files(synthetic_snapshot, tmp_path, monkeypatch):
    path, _, _ = synthetic_snapshot
    absent = tmp_path / "absent.json"
    with pytest.raises(SnapshotUnavailableError) as missing:
        read_snapshot(absent)
    assert str(absent) not in str(missing.value)

    original_open = Path.open

    def deny_selected_file(self, *args, **kwargs):
        if self == path:
            raise PermissionError("private path detail")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", deny_selected_file)
    with pytest.raises(SnapshotUnavailableError) as inaccessible:
        read_snapshot(path)
    assert str(path) not in str(inaccessible.value)
    assert "private path detail" not in str(inaccessible.value)
    monkeypatch.setattr(Path, "open", original_open)

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * (MAX_SNAPSHOT_BYTES + 1))
    with pytest.raises(SnapshotInvalidError, match="size limit"):
        read_snapshot(oversized)


def test_ds03_snapshot_is_not_a_full_series_response_and_points_match_openapi(synthetic_snapshot):
    path, _generated, _ = synthetic_snapshot
    spec = load_spec()
    loaded = read_snapshot(path)

    assert validate_schema({"$ref": "#/components/schemas/SeriesResponse"}, loaded, spec)
    for point in loaded["series"]:
        assert not validate_schema({"$ref": "#/components/schemas/SeriesPoint"}, point, spec)
