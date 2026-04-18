<template>
  <div class="statistics-page">
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>攻击类型分布</span>
          </template>
          <div ref="attackTypeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>告警趋势分析</span>
          </template>
          <div class="granularity-selector">
            <el-radio-group v-model="granularity" @change="handleGranularityChange">
              <el-radio-button label="hour">小时</el-radio-button>
              <el-radio-button label="day">天</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>源IP告警排行 TOP 10</span>
          </template>
          <el-table :data="srcIpStats" style="width: 100%">
            <el-table-column type="index" width="60"></el-table-column>
            <el-table-column prop="ip" label="源IP" min-width="150"></el-table-column>
            <el-table-column prop="count" label="告警次数" width="120">
              <template #default="{ row }">
                <el-tag type="danger">{{ row.count }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>目的IP告警排行 TOP 10</span>
          </template>
          <el-table :data="dstIpStats" style="width: 100%">
            <el-table-column type="index" width="60"></el-table-column>
            <el-table-column prop="ip" label="目的IP" min-width="150"></el-table-column>
            <el-table-column prop="count" label="告警次数" width="120">
              <template #default="{ row }">
                <el-tag type="warning">{{ row.count }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api from '../utils/api'

const granularity = ref('hour')
const attackTypeChartRef = ref(null)
const trendChartRef = ref(null)
let attackTypeChart = null
let trendChart = null
let resizeHandler = null

const attackTypeData = ref([])
const trendData = ref([])
const srcIpStats = ref([])
const dstIpStats = ref([])

const loadAttackTypes = async () => {
  try {
    const data = await api.getAttackTypes()
    attackTypeData.value = data.data || []
    updateAttackTypeChart()
  } catch (error) {
    console.error('Failed to load attack types:', error)
  }
}

const loadTrend = async () => {
  try {
    const data = await api.getTrend({ granularity: granularity.value })
    trendData.value = data.data || []
    updateTrendChart()
  } catch (error) {
    console.error('Failed to load trend:', error)
  }
}

const loadTopIPs = async () => {
  try {
    const [srcData, dstData] = await Promise.all([
      api.getTopIPs({ type: 'src', limit: 10 }),
      api.getTopIPs({ type: 'dst', limit: 10 })
    ])
    srcIpStats.value = srcData.data || []
    dstIpStats.value = dstData.data || []
  } catch (error) {
    console.error('Failed to load top IPs:', error)
  }
}

const updateAttackTypeChart = () => {
  if (!attackTypeChart) return
  const validData = attackTypeData.value.filter(d => d.attack_type).slice(0, 10)
  attackTypeChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left', top: 'middle' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['60%', '50%'],
      data: validData.map(d => ({ name: d.attack_type, value: d.count })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  })
}

const updateTrendChart = () => {
  if (!trendChart) return
  const times = trendData.value.map(d => d.time.substring(5, d.time.length))
  const total = trendData.value.map(d => d.total_alerts)
  const critical = trendData.value.map(d => d.critical || 0)
  const high = trendData.value.map(d => d.high || 0)

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['总计', '紧急', '高级'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: times, boundaryGap: false },
    yAxis: { type: 'value' },
    series: [
      { name: '总计', type: 'line', data: total, smooth: true },
      { name: '紧急', type: 'line', data: critical, smooth: true },
      { name: '高级', type: 'line', data: high, smooth: true }
    ]
  })
}

const handleGranularityChange = () => {
  loadTrend()
}

onMounted(async () => {
  await loadAttackTypes()
  await loadTrend()
  await loadTopIPs()

  if (attackTypeChartRef.value) {
    attackTypeChart = echarts.init(attackTypeChartRef.value)
    updateAttackTypeChart()
  }

  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    updateTrendChart()
  }

  resizeHandler = () => {
    attackTypeChart?.resize()
    trendChart?.resize()
  }
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
})
</script>

<style scoped>
.statistics-page {
  height: 100%;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 350px;
}

.granularity-selector {
  margin-bottom: 15px;
  text-align: center;
}
</style>
