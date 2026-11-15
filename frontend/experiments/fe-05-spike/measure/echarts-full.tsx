import * as echarts from 'echarts'

const chart = echarts.init(document.getElementById('root') as HTMLElement)
chart.setOption({ xAxis: { type: 'category', data: ['a', 'b'] }, yAxis: { type: 'value' }, series: [{ type: 'line', data: [1, null] }] })
