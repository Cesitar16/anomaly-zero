import { createRoot } from 'react-dom/client'
import { toChartPoints } from '../src/lib/chartModel'
import { SERIES } from '../src/data/fixtures'
import { SeriesChartEcharts } from '../src/components/SeriesChartEcharts'

createRoot(document.getElementById('root') as HTMLElement).render(
  <SeriesChartEcharts points={toChartPoints(SERIES)} variable="v" unit="u" selectedMonth="2005-01" onSelectMonth={() => undefined} />,
)
