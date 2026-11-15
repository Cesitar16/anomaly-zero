import hashlib
import json

import pytest

from research.ful122_inventory import inventory

FILENAME = "MERRA2_300.tavgM_2d_slv_Nx.200501.nc4"


def write_record(root, *, filename=FILENAME, manifest_filename=None, **updates):
    payload = b"clearly synthetic test fixture bytes"
    path = root / filename
    path.write_bytes(payload)
    manifest = {
        "product": {"short_name": "M2TMNXSLV", "version": "5.12.4", "variable": "T2M", "doi": "10.5067/AP1B0BA5PD2K"},
        "collection_id": "C1276812859-GES_DISC",
        "granule_id": "G1278025954-GES_DISC",
        "filename": manifest_filename or filename,
        "producer_granule_id": f"M2TMNXSLV.5.12.4:{filename}",
        "period": {"month": "2005-01", "start": "2005-01-01T00:00:00Z"},
        "source": {
            "provider": "NASA GES DISC via Earthdata CMR",
            "collection_metadata": "https://cmr.earthdata.nasa.gov/search/concepts/C1276812859-GES_DISC.umm_json",
            "granule_metadata": "https://cmr.earthdata.nasa.gov/search/concepts/G1278025954-GES_DISC.umm_json",
        },
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(manifest.get(key), dict):
            manifest[key].update(value)
        else:
            manifest[key] = value
    (root / f"{filename}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return path


def accept_fixture_payload(_path, _product, _month):
    """Test double only; it does not establish NASA provenance or scientific validity."""


def test_valid_identity_integrity_and_native_test_double_are_eligible(tmp_path):
    write_record(tmp_path)

    result = inventory([tmp_path], payload_validator=accept_fixture_payload)

    assert result["counts"]["merra2"] == 1
    assert result["matrix"][0]["triple_overlap"] is False
    record = result["records"][0]
    assert record["eligible"] is True
    assert record["found"] is True
    assert record["filename_recognized"] is True
    assert record["identified"] is True
    assert record["manifest_identity_verified"] is True
    assert record["hash_verified"] is True
    assert record["size_verified"] is True
    assert record["native_payload_verified"] is True


@pytest.mark.parametrize(
    ("updates", "reason"),
    [
        ({"product": {"short_name": "WRONG", "version": "5.12.4", "variable": "T2M"}}, "manifest_product_mismatch"),
        ({"product": {"short_name": "M2TMNXSLV", "version": "9", "variable": "T2M"}}, "manifest_version_mismatch"),
        ({"product": {"short_name": "M2TMNXSLV", "version": "5.12.4", "variable": "T10M"}}, "manifest_variable_mismatch"),
        ({"collection_id": "wrong"}, "manifest_collection_mismatch"),
        ({"producer_granule_id": "wrong"}, "manifest_producer_identity_mismatch"),
        ({"granule_id": "not-cmr"}, "cmr_granule_id_missing_or_invalid"),
        ({"source": {"collection_metadata": None, "granule_metadata": None}}, "cmr_metadata_links_missing"),
        ({"source": {"provider": "Other distributor"}}, "source_not_verified_nasa"),
        ({"source": {"granule_metadata": "https://cmr.earthdata.nasa.gov/search/concepts/G999-GES_DISC.umm_json"}}, "cmr_manifest_identity_mismatch"),
        ({"period": {"month": "2005-02"}}, "manifest_period_mismatch"),
        ({"period": {"month": "2005-01", "start": "2005-02-01T00:00:00Z"}}, "manifest_period_mismatch"),
        ({"sha256": "0" * 64}, "sha256_mismatch_or_missing"),
        ({"bytes": 1}, "size_mismatch_or_missing"),
        ({"synthetic_fixture": True}, "synthetic_fixture_not_nasa"),
    ],
)
def test_invalid_manifest_or_integrity_never_counts_as_available(tmp_path, updates, reason):
    write_record(tmp_path, **updates)

    result = inventory([tmp_path], payload_validator=accept_fixture_payload)

    assert result["counts"]["merra2"] == 0
    assert result["records"][0]["eligible"] is False
    assert reason in result["records"][0]["rejection_reasons"]
    if reason == "sha256_mismatch_or_missing":
        assert result["records"][0]["manifest_found"] is True
        assert result["records"][0]["identified"] is True
        assert result["records"][0]["hash_verified"] is False
        assert result["records"][0]["size_verified"] is True


def test_filename_must_match_manifest_and_period_is_calendar_valid(tmp_path):
    write_record(tmp_path, filename=FILENAME, manifest_filename="other.nc4")

    result = inventory([tmp_path], payload_validator=accept_fixture_payload)

    assert result["counts"]["merra2"] == 0
    assert result["records"][0]["rejection_reasons"] == ["manifest_filename_mismatch"]


def test_corrupt_payload_is_rejected(tmp_path):
    write_record(tmp_path)

    def reject_corrupt(_path, _product, _month):
        raise ValueError("native_payload_corrupt")

    record = inventory([tmp_path], payload_validator=reject_corrupt)["records"][0]

    assert record["eligible"] is False
    assert record["identified"] is True
    assert record["hash_verified"] is True
    assert record["size_verified"] is True
    assert record["native_payload_check_attempted"] is True
    assert record["native_payload_verified"] is False
    assert record["rejection_reasons"] == ["native_payload_corrupt"]


def test_identical_duplicate_collapses_and_conflicting_duplicate_excludes_month(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    write_record(first)
    write_record(second)

    identical = inventory([first, second], payload_validator=accept_fixture_payload)
    assert identical["counts"]["merra2"] == 1
    assert "duplicate_identical_granule" in identical["records"][1]["rejection_reasons"]

    changed = write_record(second)
    changed.write_bytes(b"different bytes")
    manifest_path = second / f"{FILENAME}.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(bytes=changed.stat().st_size, sha256=hashlib.sha256(changed.read_bytes()).hexdigest())
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    conflict = inventory([first, second], payload_validator=accept_fixture_payload)
    assert conflict["counts"]["merra2"] == 0
    assert all("conflicting_granules_for_product_period" in row["rejection_reasons"] for row in conflict["records"])


def test_missing_manifest_is_reported_for_identified_file(tmp_path):
    (tmp_path / FILENAME).write_bytes(b"unmanifested")

    record = inventory([tmp_path])["records"][0]

    assert record["found"] is True
    assert record["filename_recognized"] is True
    assert record["identified"] is False
    assert record["manifest_found"] is False
    assert record["hash_verified"] is False
    assert record["eligible"] is False
    assert record["rejection_reasons"] == ["manifest_missing"]


def test_invalid_calendar_month_does_not_enter_availability(tmp_path):
    filename = "MERRA2_300.tavgM_2d_slv_Nx.200513.nc4"
    write_record(tmp_path, filename=filename)

    result = inventory([tmp_path], payload_validator=accept_fixture_payload)

    assert result["counts"]["merra2"] == 0
    assert result["records"][0]["eligible"] is False
    assert "manifest_period_mismatch" in result["records"][0]["rejection_reasons"]
