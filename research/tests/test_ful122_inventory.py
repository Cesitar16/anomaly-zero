import hashlib
import json

from research.ful122_inventory import inventory


def write_granule(root, filename, manifest):
    path = root / filename
    path.write_bytes(b"synthetic fixture payload")
    (root / f"{filename}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_inventory_verifies_manifest_and_builds_monthly_overlap(tmp_path):
    cases = [
        (
            "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5",
            {"sha256": None},
        ),
        ("MERRA2_300.tavgM_2d_slv_Nx.200501.nc4", {"sha256": None}),
        ("GLDAS_NOAH025_M.A200501.021.nc4", {"sha256": None}),
    ]
    for filename, manifest in cases:
        path = tmp_path / filename
        path.write_bytes(b"synthetic fixture payload")
        product = "imerg_final" if filename.startswith("3B-") else "merra2" if filename.startswith("MERRA") else "gldas"
        manifest.update(
            {
                "product": {"key": product},
                "period": {"month": "2005-01"},
                "filename": filename,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        (tmp_path / f"{filename}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = inventory([tmp_path])

    assert result["counts"] == {"imerg_final": 1, "merra2": 1, "gldas": 1}
    assert result["matrix"] == [
        {"period": "2005-01", "imerg_final": True, "merra2": True, "gldas": True, "triple_overlap": True}
    ]
    assert all(record["manifest_hash_matches"] for record in result["records"])
    assert all(record["manifest_size_matches"] for record in result["records"])


def test_inventory_does_not_mark_bad_hash_as_verified(tmp_path):
    filename = "MERRA2_300.tavgM_2d_slv_Nx.200501.nc4"
    path = write_granule(tmp_path, filename, {"product": {"key": "merra2"}, "period": {"month": "2005-01"}, "sha256": "bad", "bytes": 25})

    record = inventory([tmp_path])["records"][0]

    assert record["bytes"] == path.stat().st_size
    assert record["manifest_hash_matches"] is False
    assert record["manifest_size_matches"] is True
