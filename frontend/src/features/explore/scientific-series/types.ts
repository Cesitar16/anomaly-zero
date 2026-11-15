/** Minimal structural view of OpenAPI SeriesResponse required by the panel.
 * A complete SeriesResponse is assignable to this type; this is not a second
 * transport model and the component never fetches or transforms units.
 */
export type ScientificDataState = 'available' | 'available_with_gaps' | 'no_data'

export interface ScientificProviderFlag {
  name: string
  value: unknown
}

export interface ScientificPointQuality {
  state?: 'unassessed' | 'missing' | 'unknown' | string
  provider_flags?: readonly ScientificProviderFlag[]
  missing_reason?: string | null
}

export interface ScientificSeriesPoint {
  date: string
  value: number | null
  quality?: ScientificPointQuality | null
}

export interface ScientificProductSource {
  agency?: string
  distributor?: string | null
  collection_id?: string | null
  doi?: string | null
  source_urls?: readonly string[]
  granule_ids?: readonly string[]
}

export interface ScientificSeriesProduct {
  product_id?: string
  short_name?: string
  product_version?: string
  variable?: string
  quantity?: string
  unit?: string
  source?: ScientificProductSource | null
}

export interface ScientificSupport {
  support_type?: string
  approval_state?: string
  method?: string | null
  area_weighted?: boolean | null
  weighting_reference?: string | null
  mask_version?: string | null
  point?: {
    cell_id?: string
    latitude?: number | null
    longitude?: number | null
  } | null
}

export interface ScientificProvenance {
  source_sha256?: readonly string[]
  retrieved_at?: string | null
  source_updated_at?: string | null
  snapshot_created_at?: string | null
  manifest_version?: string | null
  manifest_sha256?: string | null
  original_file_count?: number | null
}

export interface ScientificResponseQuality {
  source_flag_fields?: readonly string[]
  provider_flags_applied?: boolean
  verification_state?: string
}

/** Subset of the integrated SeriesResponse; omitted optional response fields are accepted. */
export interface ScientificSeriesResponse {
  synthetic: boolean
  data_state: ScientificDataState
  product: ScientificSeriesProduct
  series: readonly ScientificSeriesPoint[]
  dataset_id?: string | null
  quality?: ScientificResponseQuality | null
  spatial_aggregation?: ScientificSupport | null
  provenance?: ScientificProvenance | null
  coverage?: {
    missing_periods?: readonly string[]
  } | null
  requested_coverage?: {
    start?: string
    end?: string
  } | null
  region?: {
    region_id?: string
    name?: string
  }
}

export interface ScientificSeriesPanelProps {
  response: ScientificSeriesResponse
  className?: string
}

export interface PlotPoint {
  month: string
  date: string
  value: number | null
  qualityState: string
  missingReason: string | null
  flags: readonly ScientificProviderFlag[]
  invalidValue: boolean
}
