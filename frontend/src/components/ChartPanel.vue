<template>
  <div ref="chartRef" class="chart-panel"></div>
</template>

<script setup>
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  chartData: {
    type: Object,
    default: () => ({})
  },
  chartType: {
    type: String,
    default: 'bar'
  }
})

const chartRef = ref(null)
let chartInstance = null

function renderChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const categories = props.chartData?.categories || []
  const series = props.chartData?.series || []

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 24, right: 24, top: 32, bottom: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: '#4c657f' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#4c657f' }
    },
    series: series.map((item) => ({
      name: item.name,
      type: props.chartType,
      smooth: props.chartType === 'line',
      data: item.data,
      itemStyle: { color: '#4a90e2' },
      areaStyle: props.chartType === 'line' ? { color: 'rgba(74, 144, 226, 0.18)' } : undefined
    }))
  })
}

onMounted(async () => {
  await nextTick()
  renderChart()
  window.addEventListener('resize', renderChart)
})

watch(
  () => [props.chartData, props.chartType],
  async () => {
    await nextTick()
    renderChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderChart)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.chart-panel {
  width: 100%;
  height: 360px;
}
</style>
