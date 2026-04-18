<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card total">
          <div class="stat-content">
            <div class="stat-icon"><Warning /></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_alerts || 0 }}</div>
              <div class="stat-label">总告警数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card critical">
          <div class="stat-content">
            <div class="stat-icon"><CircleClose /></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.critical_count || 0 }}</div>
              <div class="stat-label">紧急告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card high">
          <div class="stat-content">
            <div class="stat-icon"><CloseBold /></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.high_count || 0 }}</div>
              <div class="stat-label">高级告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card medium">
          <div class="stat-content">
            <div class="stat-icon"><WarningFilled /></div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.medium_count || 0 }}</div>
              <div class="stat-label">中级告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>告警趋势（最近24小时）</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>攻击类型分布</span>
          </template>
          <div ref="pieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最新告警</span>
          </template>
          <el-table :data="recentAlerts" style="width: 100%" :max-height="400">
            <el-table-column prop="timestamp" label="时间" width="180" :formatter="formatTime"></el-table-column>
            <el-table-column prop="src_ip" label="源IP" width="140"></el-table-column>
            <el-table-column prop="dst_ip" label="目的IP" width="140"></el-table-column>
            <el-table-column prop="protocol" label="协议" width="80"></el-table-column>
            <el-table-column prop="severity" label="级别" width="80" :formatter="formatSeverity"></el-table-column>
            <el-table-column prop="signature" label="告警签名" min-width="200"></el-table-column>
            <el-table-column prop="category" label="分类" width="120"></el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Warning, CircleClose, CloseBold, WarningFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { io } from 'socket.io-client'
import api from '../utils/api'

const stats = ref({
  total_alerts: 0,
  critical_count: 0,
  high_count: 0,
  medium_count: 0,
  low_count: 0
})
const recentAlerts = ref([])
const trendData = ref([])
const attackTypeData = ref([])

const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null
let resizeHandler = null

let socket = null

const formatTime = (row) => {
  return new Date(row.timestamp).toLocaleString('zh-CN')
}

const formatSeverity = (row) => {
  const map = { 1: '紧急', 2: '高', 3: '中', 4: '低' }
  return map[row.severity] || '未知'
}

const loadDashboardData = async () => {
  try {
    const data = await api.getDashboardStats()
    stats.value = {
      total_alerts: data.total_alerts,
      critical_count: data.critical_count,
      high_count: data.high_count,
      medium_count: data.medium_count,
      low_count: data.low_count
    }
    recentAlerts.value = data.recent_alerts || []
    trendData.value = data.last_24_hours || []
    updateTrendChart()
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

const loadAttackTypes = async () => {
  try {
    const data = await api.getAttackTypes()
    attackTypeData.value = data.data || []
    updatePieChart()
  } catch (error) {
    console.error('Failed to load attack types:', error)
  }
}

const updateTrendChart = () => {
  if (!trendChart) return
  const hours = trendData.value.map(d => {
    const date = new Date(d.hour)
    return `${date.getHours()}:00`
  })
  const values = trendData.value.map(d => d.total_alerts)

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: hours },
    yAxis: { type: 'value', name: '告警数' },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#409EFF' }
    }]
  })
}

const updatePieChart = () => {
  if (!pieChart) return
  const validData = attackTypeData.value.filter(d => d.attack_type)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: validData.slice(0, 8).map(d => ({ name: d.attack_type, value: d.count }))
    }]
  })
}

onMounted(async () => {
  await loadDashboardData()
  await loadAttackTypes()

  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    updateTrendChart()
  }

  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    updatePieChart()
  }

  resizeHandler = () => {
    trendChart?.resize()
    pieChart?.resize()
  }
  window.addEventListener('resize', resizeHandler)

  socket = io('/', {
    transports: ['websocket', 'polling']
  })

  socket.on('connect', () => {
    console.log('WebSocket connected')
  })

  socket.on('new_alert', (data) => {
    recentAlerts.value.unshift(data)
    if (recentAlerts.value.length > 10) {
      recentAlerts.value.pop()
    }
    stats.value.total_alerts++
    if (data.severity === 1) stats.value.critical_count++
    else if (data.severity === 2) stats.value.high_count++
    else if (data.severity === 3) stats.value.medium_count++
    else stats.value.low_count++
  })

  socket.on('stats_update', (data) => {
    stats.value = data
  })
})

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
})
</script>

<style scoped>
.dashboard {
  height: 100%;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  font-size: 48px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.stat-card.total .stat-icon {
  color: #409EFF;
}

.stat-card.critical .stat-icon {
  color: #F56C6C;
}

.stat-card.high .stat-icon {
  color: #E6A23C;
}

.stat-card.medium .stat-icon {
  color: #E6A23C;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 300px;
}
</style>
