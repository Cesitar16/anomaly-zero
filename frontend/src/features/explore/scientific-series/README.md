# ScientificSeriesPanel

Reusable, presentational monthly NASA series panel. It performs no HTTP requests and no scientific unit conversion, aggregation, interpolation, inference, or prediction.

```tsx
import { ScientificSeriesPanel } from '../features/explore/scientific-series'

<ScientificSeriesPanel response={seriesResponse} />
```

`response` accepts a structural subset of the OpenAPI `SeriesResponse` (full response objects are assignable):

- Required: `synthetic`, `data_state` (`available | available_with_gaps | no_data`), `product`, `series`.
- Product: optional display identity (`short_name`, `product_id`, `product_version`, `variable`, `quantity`, `unit`) and provenance (`source.agency`, `collection_id`, `doi`, `granule_ids`).
- Every point requires ISO-like `date` and `value: number | null`; optional `quality.state`, `missing_reason`, and `provider_flags` are shown without treating unknown QA as passed.
- Optional `quality.verification_state`, `spatial_aggregation.support_type`, `provenance`, `coverage`, and `region` are defensive metadata.
- Optional `className` adds a wrapper class.

Zeros render as numeric zero; nulls and non-finite values remain gaps and break the line (`connectNulls={false}`). Non-finite values are marked in the table and are never passed to Recharts as numbers. A `no_data` response suppresses all payload observations and the chart, even if its series array is inconsistent. `synthetic: true` always displays an explicit synthetic-data notice. The HTML table is the accessible equivalent of the chart and remains available on narrow screens. `point_sample` and absence of approved regional aggregation are called out explicitly; provider QA application is not treated as scientific approval.

Tests use only clearly labeled synthetic fixtures.
