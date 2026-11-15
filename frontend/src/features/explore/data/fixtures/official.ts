/**
 * Ejemplos OFICIALES del contrato AZ-04 (docs/openapi-contract-v0.yaml), copiados sin cambios.
 * Todos son sintéticos (`synthetic: true`): no son observaciones NASA ni resultados estadísticos.
 * `test/contracts.test.ts` comprueba que sigan idénticos a los del YAML y que validen contra sus esquemas.
 * Si el contrato cambia, hay que actualizar este archivo (y pedir validación a César).
 */
import type { ErrorResponse, SeriesResponse } from '../../types/contracts'

/** Serie de tres meses: una celda (no un promedio), con un faltante y un cero legítimo. */
export const seriesPointSample: SeriesResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "data_state": "available_with_gaps",
  "region": {
    "region_id": "REG01",
    "name": "Región sintética",
    "geometry_version": null,
    "geometry_source": null,
    "crs": null,
    "area_km2": null
  },
  "product": {
    "product_id": "P02",
    "short_name": "GPM_3IMERGM",
    "product_version": "V07B",
    "variable": "precipitation",
    "quantity": "monthly_mean_rate",
    "unit": "mm/hr",
    "availability": "partial",
    "source": {
      "agency": "NASA/JAXA",
      "distributor": "GES DISC",
      "collection_id": "C2723754851-GES_DISC",
      "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
      "source_urls": [],
      "granule_ids": []
    },
    "current_dataset_id": "ds-synthetic-001",
    "coverage": {
      "start": "2005-01",
      "end": "2005-03"
    },
    "quality": {
      "source_flag_fields": [],
      "provider_flags_applied": false,
      "source_missing_attributes": {
        "fill_value": -9999.9,
        "missing_value": null,
        "scale_factor": null,
        "add_offset": null
      },
      "finite_non_fill_filter_applied": true,
      "verification_state": "basic_checks_only",
      "mask_applied": null
    }
  },
  "dataset_id": "ds-synthetic-001",
  "provenance": {
    "source_sha256": [],
    "retrieved_at": null,
    "manifest_version": null,
    "source_updated_at": null,
    "snapshot_created_at": null,
    "manifest_sha256": null,
    "original_file_count": null
  },
  "temporal": {
    "frequency": "monthly",
    "calendar": null,
    "date_label": "month_start"
  },
  "requested_coverage": {
    "start": "2005-01",
    "end": "2005-03",
    "end_inclusive": true
  },
  "available_coverage": {
    "start": "2005-01",
    "end": "2005-03"
  },
  "coverage": {
    "expected_periods": 3,
    "present_periods": 3,
    "valid_periods": 2,
    "missing_periods": [
      "2005-02"
    ]
  },
  "quality": {
    "source_flag_fields": [],
    "provider_flags_applied": false,
    "source_missing_attributes": {
      "fill_value": -9999.9,
      "missing_value": null,
      "scale_factor": null,
      "add_offset": null
    },
    "finite_non_fill_filter_applied": true,
    "verification_state": "basic_checks_only",
    "mask_applied": null
  },
  "spatial_aggregation": {
    "support_type": "point_sample",
    "approval_state": "not_assessed",
    "method": null,
    "area_weighted": null,
    "weighting_reference": null,
    "mask_version": null,
    "point": {
      "cell_id": "cell-synthetic-001",
      "latitude": null,
      "longitude": null
    }
  },
  "transformations": [],
  "series": [
    {
      "date": "2005-01-01",
      "value": 0.42,
      "quality": {
        "state": "unassessed",
        "provider_flags": [],
        "missing_reason": null
      }
    },
    {
      "date": "2005-02-01",
      "value": null,
      "quality": {
        "state": "missing",
        "provider_flags": [],
        "missing_reason": "provider_fill_value"
      }
    },
    {
      "date": "2005-03-01",
      "value": 0,
      "quality": {
        "state": "unassessed",
        "provider_flags": [],
        "missing_reason": null
      }
    }
  ],
  "generated_at": "2026-01-01T00:00:00Z"
}

/** HTTP 200 con `data_state: no_data` (no es un error). */
export const seriesNoData: SeriesResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "data_state": "no_data",
  "region": {
    "region_id": "REG01",
    "name": "Región sintética",
    "geometry_version": null,
    "geometry_source": null,
    "crs": null,
    "area_km2": null
  },
  "product": {
    "product_id": "P03",
    "short_name": "GLDAS_NOAH025_M",
    "product_version": "2.1",
    "variable": "SoilMoi0_10cm_inst",
    "quantity": "soil_moisture_layer_0_10_cm",
    "unit": "kg m-2",
    "availability": "unavailable",
    "source": {
      "agency": "NASA",
      "distributor": "GES DISC",
      "collection_id": "C1342986036-GES_DISC",
      "doi": "10.5067/SXAVCZFAQLNO",
      "source_urls": [],
      "granule_ids": []
    },
    "current_dataset_id": null,
    "coverage": null,
    "quality": null
  },
  "dataset_id": null,
  "provenance": null,
  "temporal": {
    "frequency": "monthly",
    "calendar": null,
    "date_label": "month_start"
  },
  "requested_coverage": {
    "start": "2005-01",
    "end": "2005-03",
    "end_inclusive": true
  },
  "available_coverage": null,
  "coverage": {
    "expected_periods": 3,
    "present_periods": 0,
    "valid_periods": 0,
    "missing_periods": [
      "2005-01",
      "2005-02",
      "2005-03"
    ]
  },
  "quality": {
    "source_flag_fields": [],
    "provider_flags_applied": false,
    "source_missing_attributes": {
      "fill_value": null,
      "missing_value": null,
      "scale_factor": null,
      "add_offset": null
    },
    "finite_non_fill_filter_applied": false,
    "verification_state": "unassessed",
    "mask_applied": null
  },
  "spatial_aggregation": null,
  "transformations": [],
  "series": [],
  "message": "No hay datos disponibles para el período solicitado.",
  "generated_at": "2026-01-01T00:00:00Z"
}

/** HTTP 422 `INVALID_PARAMETER`. */
export const error422InvalidParameter: ErrorResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-01-01T00:00:00Z",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "El formato del mes debe ser YYYY-MM.",
    "retryable": false,
    "request_id": "req-synthetic-invalid-001",
    "details": {
      "field": "start",
      "received": "2005-13"
    }
  }
}

/** HTTP 503 `SERVICE_UNAVAILABLE`, reintentable. */
export const error503SnapshotUnavailable: ErrorResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "El snapshot de datos no está disponible temporalmente.",
    "retryable": true,
    "request_id": "req-synthetic-001",
    "details": {
      "dataset_id": "ds-synthetic-001",
      "provider_status": null
    }
  },
  "generated_at": "2026-01-01T00:00:00Z"
}

/** HTTP 409 `ANALYSIS_METHOD_UNAVAILABLE`: no se creó ningún análisis. */
export const error409MethodUnavailable: ErrorResponse = {
  "contract_version": "0.1-draft",
  "synthetic": true,
  "generated_at": "2026-01-01T00:00:00Z",
  "error": {
    "code": "ANALYSIS_METHOD_UNAVAILABLE",
    "message": "No hay un método estadístico aprobado y habilitado; no se creó un análisis.",
    "retryable": false,
    "request_id": "req-synthetic-analysis-001",
    "details": {
      "analysis": {
        "state": "not_available",
        "analysis_id": null,
        "dataset_id": "ds-synthetic-001",
        "region_id": "REG01",
        "product_id": "P02",
        "window": {
          "start": "2005-01",
          "end": "2005-03",
          "end_inclusive": true
        },
        "method": null,
        "metrics": {
          "slope": null,
          "slope_unit": null,
          "confidence_interval": null,
          "p_value": null,
          "significance": null
        }
      }
    }
  }
}
