import { describe, expect, it } from 'vitest'
import { hasVerifiedContextGeometry, pointFromSupport, toMapLibreCoordinates } from '../../features/explore/lib/contextMap'
import type { ContextGeometryOverlay } from '../../features/explore/lib/contextMap'
import type { PointSampleSupport } from '../../features/explore/types/contracts'

function point(latitude: number | null, longitude: number | null): PointSampleSupport {
  return {
    support_type: 'point_sample',
    approval_state: 'not_assessed',
    method: null,
    area_weighted: null,
    weighting_reference: null,
    mask_version: null,
    point: { cell_id: 'synthetic-test-cell', latitude, longitude },
  }
}

describe('coordenadas del mapa contextual', () => {
  it('acepta solo coordenadas finitas en rangos geográficos', () => {
    const resolved = pointFromSupport(point(-35.11, 147.36))
    expect(resolved).toEqual({ latitude: -35.11, longitude: 147.36, cellId: 'synthetic-test-cell' })
    expect(toMapLibreCoordinates(resolved!)).toEqual([147.36, -35.11])
    expect(pointFromSupport(point(null, 147.36))).toBeNull()
    expect(pointFromSupport(point(Number.NaN, 147.36))).toBeNull()
    expect(pointFromSupport(point(-91, 147.36))).toBeNull()
    expect(pointFromSupport(point(-35.11, 181))).toBeNull()
  })

  it('rechaza geometría sin procedencia verificable, CRS GeoJSON esperado o hash', () => {
    const fixture: ContextGeometryOverlay = {
      label: 'Synthetic test boundary',
      attribution: 'Fixture local de tests; no representa el límite oficial',
      sourceUrl: 'https://example.invalid/test-fixture',
      licenseName: 'Test fixture only',
      licenseUrl: 'https://example.invalid/license',
      sha256: 'a'.repeat(64),
      data: {
        type: 'FeatureCollection',
        features: [{
          type: 'Feature',
          properties: { synthetic: true },
          geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] },
        }],
      },
    }
    expect(hasVerifiedContextGeometry(fixture)).toBe(true)
    expect(hasVerifiedContextGeometry({ ...fixture, sha256: 'no-hash' })).toBe(false)
    expect(hasVerifiedContextGeometry({ ...fixture, sourceUrl: 'javascript:alert(1)' })).toBe(false)
    expect(hasVerifiedContextGeometry({ ...fixture, data: { type: 'FeatureCollection', features: [] } })).toBe(false)
    expect(hasVerifiedContextGeometry(null)).toBe(false)
  })
})
