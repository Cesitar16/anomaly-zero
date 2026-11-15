import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ScientificSeriesPanel } from './ScientificSeriesPanel'
import type { ScientificSeriesResponse } from './types'

// Synthetic fixture only: values below are for component behavior tests, not NASA observations.
const syntheticResponse: ScientificSeriesResponse = {
  synthetic: true,
  data_state: 'available_with_gaps',
  product: {
    short_name: 'TEST-SYNTHETIC',
    product_version: 'fixture-1',
    variable: 'test_variable',
    unit: 'K',
    source: { agency: 'Synthetic fixture', collection_id: 'TEST', doi: '10.0000/synthetic' },
  },
  spatial_aggregation: { support_type: 'point_sample' },
  quality: { verification_state: 'unassessed' },
  series: [
    { date: '2005-01-01', value: 0, quality: { state: 'unassessed' } },
    { date: '2005-02-01', value: null, quality: { state: 'missing', missing_reason: 'synthetic gap' } },
  ],
}

describe('ScientificSeriesPanel', () => {
  it('preserves zero and null distinctly in its accessible data table', () => {
    render(<ScientificSeriesPanel response={syntheticResponse} />)
    expect(screen.getByRole('row', { name: /ene 2005.*0 K.*No evaluada/i })).toBeTruthy()
    expect(screen.getByRole('row', { name: /feb 2005.*Sin dato.*Dato faltante.*synthetic gap/i })).toBeTruthy()
    expect(screen.getByText(/huecos no se interpolan/i)).toBeTruthy()
  })

  it('identifies synthetic data, provenance, version, and unapproved QA and spatial support', () => {
    render(<ScientificSeriesPanel response={syntheticResponse} />)
    expect(screen.getByText(/Datos sintéticos · no son observaciones NASA/)).toBeTruthy()
    expect(screen.getByText(/no representa un promedio regional/i)).toBeTruthy()
    expect(screen.getByText(/QA del proveedor no está aplicada o aprobada/i)).toBeTruthy()
    expect(screen.getByText(/versión fixture-1/i)).toBeTruthy()
    expect(screen.getByRole('table')).toBeTruthy()
    expect(screen.getByRole('columnheader', { name: /Valor \(K\)/ })).toBeTruthy()
  })

  it('renders an honest no-data state without observations', () => {
    render(<ScientificSeriesPanel response={{ ...syntheticResponse, data_state: 'no_data', series: [] }} />)
    expect(screen.getByText(/No hay observaciones que graficar/i)).toBeTruthy()
    expect(screen.getByText(/Sin filas: no hay observaciones/i)).toBeTruthy()
  })

  it('creates explicit null rows for absent monthly periods in requested coverage', () => {
    render(<ScientificSeriesPanel response={{
      ...syntheticResponse,
      data_state: 'available_with_gaps',
      requested_coverage: { start: '2005-01', end: '2005-03' },
      series: [
        { date: '2005-01-01', value: 1, quality: { state: 'unassessed' } },
        { date: '2005-03-01', value: 3, quality: { state: 'unassessed' } },
      ],
    }} />)
    expect(screen.getByRole('row', { name: /feb 2005.*Sin dato.*Dato faltante.*Período mensual ausente/i })).toBeTruthy()
  })

  it('handles absent optional provenance and QA attributes defensively', () => {
    const response: ScientificSeriesResponse = {
      synthetic: false,
      data_state: 'available',
      product: {},
      series: [{ date: '2005-01-01', value: 2 }],
    }
    render(<ScientificSeriesPanel response={response} />)
    expect(screen.getAllByText(/No informada/).length).toBeGreaterThan(0)
    expect(screen.getByText(/^2$/)).toBeTruthy()
  })
})
