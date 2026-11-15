import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ScientificSeriesPanel } from './ScientificSeriesPanel'
import type { ScientificSeriesResponse } from './types'

vi.mock('recharts', async () => {
  const React = await import('react')
  const chart = ({ children, data }: { children?: React.ReactNode; data?: Array<{ plotValue: number | null }> }) =>
    React.createElement('div', { 'data-testid': 'mock-line-chart', 'data-values': JSON.stringify(data?.map((point) => point.plotValue)) }, children)
  const container = ({ children }: { children?: React.ReactNode }) => React.createElement('div', null, children)
  return {
    CartesianGrid: () => null,
    Line: () => null,
    LineChart: chart,
    ResponsiveContainer: container,
    Tooltip: () => null,
    XAxis: () => null,
    YAxis: () => null,
  }
})

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
    expect(screen.getByText(/QA del proveedor no equivale a aprobación científica/i)).toBeTruthy()
    expect(screen.getByText(/versión fixture-1/i)).toBeTruthy()
    expect(screen.getByRole('table')).toBeTruthy()
    expect(screen.getByRole('columnheader', { name: /Valor \(K\)/ })).toBeTruthy()
  })

  it('renders an honest no-data state without observations', () => {
    render(<ScientificSeriesPanel response={{ ...syntheticResponse, data_state: 'no_data', series: [] }} />)
    expect(screen.getByText(/No hay observaciones que graficar/i)).toBeTruthy()
    expect(screen.getByText(/Sin filas: no hay observaciones/i)).toBeTruthy()
  })

  it('keeps NaN and infinite source values out of Recharts and warns in the table', () => {
    render(<ScientificSeriesPanel response={{
      ...syntheticResponse,
      data_state: 'available',
      series: [
        { date: '2005-01-01', value: Number.NaN },
        { date: '2005-02-01', value: Number.POSITIVE_INFINITY },
        { date: '2005-03-01', value: Number.NEGATIVE_INFINITY },
        { date: '2005-04-01', value: 0 },
      ],
    }} />)
    expect(screen.getByTestId('mock-line-chart').getAttribute('data-values')).toBe('[null,null,null,0]')
    expect(screen.getByRole('table').textContent).toContain('Valor no finito (NaN); ocultado del gráfico')
    expect(screen.getByRole('table').textContent).toContain('Valor no finito (Infinity); ocultado del gráfico')
    expect(screen.getByRole('table').textContent).toContain('Valor no finito (-Infinity); ocultado del gráfico')
  })

  it('suppresses inconsistent observations when data_state is no_data', () => {
    render(<ScientificSeriesPanel response={{
      ...syntheticResponse,
      data_state: 'no_data',
      series: [{ date: '2005-01-01', value: 99, quality: { state: 'unassessed' } }],
    }} />)
    expect(screen.queryByTestId('mock-line-chart')).toBeNull()
    expect(screen.queryByRole('row', { name: /ene 2005/i })).toBeNull()
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

  it('does not treat provider QA application as scientific approval', () => {
    render(<ScientificSeriesPanel response={{
      ...syntheticResponse,
      quality: { verification_state: 'provider_qa_applied' },
    }} />)
    expect(screen.getAllByText(/sin aprobación científica/i).length).toBeGreaterThan(0)
  })
})
