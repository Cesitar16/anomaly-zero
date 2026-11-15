import { createRoot } from 'react-dom/client'
import { toChartPoints } from '../src/lib/chartModel'
import { SERIES } from '../src/data/fixtures'
import { SeriesChartRecharts } from '../src/components/SeriesChartRecharts'

createRoot(document.getElementById('root') as HTMLElement).render(
  <SeriesChartRecharts points={toChartPoints(SERIES)} variable="v" unit="u" selectedMonth="2005-01" onSelectMonth={() => undefined} />,
)
