import numpy as np
import pytest
import shapely

from research.auditar_espacial_ful104 import (
    REQUIRED_SAMPLE_NAMES,
    require_samples,
    spatial_selection_masks,
    valid_data_mask,
    validate_results,
)


def test_valid_data_mask_matches_float32_fill_representation():
    fill = np.float32(-9999.9)
    values = np.array([1.25, fill, np.nan], dtype=np.float32)

    np.testing.assert_array_equal(valid_data_mask(values, float(fill)), [True, False, False])


def test_valid_data_mask_handles_integer_fill_values():
    values = np.array([0, -9999, 4], dtype=np.int16)

    np.testing.assert_array_equal(valid_data_mask(values, -9999), [True, False, True])


def test_spatial_selection_distinguishes_centers_from_intersections():
    basin = shapely.box(0, 0, 1, 1)
    cells = np.array(
        [
            shapely.box(0.2, 0.2, 0.8, 0.8),
            shapely.box(0.8, 0.2, 1.4, 0.8),
            shapely.box(1.1, 0.2, 1.5, 0.8),
        ],
        dtype=object,
    )

    centers, intersects = spatial_selection_masks(
        basin, cells, np.array([0.5, 1.1, 1.3]), np.array([0.5, 0.5, 0.5])
    )

    np.testing.assert_array_equal(centers, [True, False, False])
    np.testing.assert_array_equal(intersects, [True, True, False])


def test_require_samples_fails_when_a_required_sample_is_missing(tmp_path):
    for name in REQUIRED_SAMPLE_NAMES[:-1]:
        (tmp_path / name).touch()

    with pytest.raises(FileNotFoundError, match=REQUIRED_SAMPLE_NAMES[-1]):
        require_samples(tmp_path)


def test_validate_results_fails_when_a_sample_was_not_processed():
    results = [{"file": REQUIRED_SAMPLE_NAMES[0], "error": "unreadable"}]

    with pytest.raises(RuntimeError, match="Auditoría incompleta"):
        validate_results(results)
